# kết nối modbus tcp
'''
Nút 1 : bật hàn
Nút 2 : tắt hàn 
Nút 3 : move L  
Nút 4 : move J
Nút 5 : move C
Nút 6 : Lưu điểm hiện tại với hai đặc tính đã nhập ở trên
Nút 7 : start/stop
Nút 8 : clear
nhớ là cần tool calibration nữa mới chạy được.
'''

import time
from tkinter import *
from Robotic_Arm.rm_robot_interface import *
from modbus import PLCStation

# Khởi tạo
robot = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
handle = robot.rm_create_robot_arm("192.168.1.18", 8080)
print("robotic arm ID:", handle.id)

# Lấy thông tin phần mềm robot
software_info = robot.rm_get_arm_software_info()
if software_info[0] == 0:
    print("\n================== Arm Software Information ==================")
    print("Arm Model: ", software_info[1]['product_version'])
    print("Algorithm Library Version: ", software_info[1]['algorithm_info']['version'])
    print("Control Layer Software Version: ", software_info[1]['ctrl_info']['version'])
    print("Dynamics Version: ", software_info[1]['dynamic_info']['model_version'])
    print("Planning Layer Software Version: ", software_info[1]['plan_info']['version'])
    print("==============================================================\n")
else:
    print("\nFailed to get arm software information, Error code: ", software_info[0], "\n")
'''
# set up tool frame :
frame = rm_frame_t('weld_gun',[-41.704/1000,-22.663/1000,317.572/1000,-0.05,-0.369,-2.326],enable=1, is_tcp=1, payload=1.983, cx= -48/1000, cy= -60/1000, cz= 65/1000)
state_tool = robot.rm_set_manual_tool_frame(frame)
print("Set tool frame:", "Success" if state_tool == 0 else f"Failed, code {state_tool}")
'''

# 🚀 Hiệu chuẩn tool weld_gun
tool_config = ToolCoordinateConfig()
tool_config.handle = handle  # Gán handle robot vào class

# Tạo struct rm_frame_t
frame = rm_frame_t()
frame.name = b"weld_gun"    # Tên tool
frame.x = -41.704 / 1000    # mm -> m
frame.y = -22.663 / 1000
frame.z = 317.572 / 1000
frame.rx = -0.050
frame.ry = -0.369
frame.rz = -2.326
frame.payload = 1.983       # kg
frame.cx = -48.000 / 1000
frame.cy = -60.000 / 1000
frame.cz = 64.999 / 1000

# Gửi cấu hình vào robot
ret = tool_config.rm_set_manual_tool_frame(frame)
# Kiểm tra kết quả
if ret == 0:
    print("✅ Tool 'weld_gun' đã được cấu hình thành công.")
else:
    print(f"❌ Lỗi khi cấu hình tool 'weld_gun', mã lỗi: {ret}")

# 👉 Chuyển sang tool vừa cấu hình nếu cần
ret = tool_config.rm_change_tool_frame("weld_gun")
if ret == 0:
    print("✅ Đã chuyển sang tool coordinate system 'weld_gun'")
else:
    print(f"❌ Không thể chuyển sang tool 'weld_gun', mã lỗi: {ret}")


# tạo đối tượng để in/out từ modbus
plc = PLCStation(serial_port="COM5", baudrate=9600, timeout=1)    

def get_current_pose():
    state_pose, cur_pose = robot.rm_get_current_arm_state()
    return cur_pose['pose'] if state_pose == 0 else None

# đảm bảo nhấn lưu thì chỉ lưu một điểm duy nhất.
flag_save_point = False  
# khởi tạo trước moveJ và tắt hàn
move_type = 'J'
plc_choice = 0 
point_list = []
# lưu tọa độ, trạng thái của các điểm.
def save_point(input_states):
    pose = get_current_pose()
    if not pose:
        print("Không lấy được điểm !")
        return
    
    # khi được nhấn sẽ nhảy lên mức 1  
    if input_states[0]:
        # nút 1 được nhấn, trả tín hiệu bật hàn
        plc_choice = 1
    if input_states[1]:
        # nút 2 được nhấn, trả tín hiệu tắt hàn
        plc_choice = 0 
    plc_outputs = {
        "1": [True, False, False, False, False],
        "0": [False, False, False, False, False]
    }
    # mặc định ko tìm thấy là tắt.
    plc_out = plc_outputs.get(plc_choice, [False]*5)   
    
    if input_states[2]:
        # nút 3 được nhấn, trả tín hiệu đi thẳng : moveL
        move_type = "L"
    if input_states[3]:
        # nút 4 được nhấn, trả tín hiệu đi cong : moveJ
        move_type = "J"
    if input_states[4]:
        # nút 4 được nhấn, trả tín hiệu đi cong : moveC
        move_type = "C"
    
    if input_states[5] and not flag_save_point:
        # nút 6 được nhấn, lưu lại trạng thái các điểm vào poit_list
        flag_save_point = True
        point_list.append({
            "pose": pose,
            "on_off": plc_out,
            "move_type": move_type
        })
        print("lưu điểm thành công")
    if not input_states[5] and flag_save_point:
        flag_save_point = False

def run_robot_follow_point_list():
    for pt in point_list:
        # tương ứng mỗi pose ( điểm đến ) : ta cho robot di chuyển tới đó
        pose = pt['pose']
        move_style = pt['move_type']
        if move_style == "L":
            robot.rm_movel(pose, v=10, r=0, connect=0, block=1)
        if move_style == "J":
            robot.rm_movej_p(pose, v=10, r=0, connect=0, block=1)
        # if move_style == 'C':
            # chức năng này phát triển sau.

        # sau khi đã tới một pose (điểm đến) : bật/tắt hàn tại đây
        plc.write_datas_output(254, pt["on_off"])
        time.sleep(0.5)
 

while True:
    # đọc tín hiệu của 8 chân đầu vào
    input_states = plc.read_datas_input(slave_id = 254,count = 8)
    for i in range(4):
        if input_states[i]:
            save_point(input_states)
    if input_states[6]:
        # ctrinh sẽ bị dừng ở phần này, vì robot dùng block
        # di chuyển đến từng điểm trong poit_list và bật/tắt hàn tại điểm đó
        # sau khi chạy xong một lượt point_list sẽ dừng lại.
        run_robot_follow_point_list()
        break
        
    if input_states[7]:
        point_list = []
    time.sleep(0.1)