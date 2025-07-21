from Robotic_Arm.rm_robot_interface import *

# ⚙️ Khởi tạo robot
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

# 🚀 Hiệu chuẩn tool weld_gun
tool_config = ToolCoordinateConfig()
tool_config.handle = handle  # Gán handle robot vào class

# Tạo struct rm_frame_t
frame = rm_frame_t()
frame.name = b"weld_gun"  # Tên tool
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

