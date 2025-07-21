from Robotic_Arm.rm_robot_interface import *

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

def check_robot_ready():
    # 🔌 Kiểm tra trạng thái servo
    status_power = robot.rm_get_arm_power_state()
    power_state = status_power[1] if isinstance(status_power, tuple) else status_power

    # 🏁 Kiểm tra chế độ chạy
    status_mode = robot.rm_get_arm_run_mode()
    run_mode = status_mode[1] if isinstance(status_mode, tuple) else status_mode

    # ⚠️ Kiểm tra lỗi hệ thống
    arm_state = robot.rm_get_current_arm_state()
    err_code = arm_state[1]['err'] if isinstance(arm_state, tuple) else "UNKNOWN"

    # Hiển thị trạng thái
    if power_state != 1:
        print("❌ Servo đang TẮT. Không thể điều khiển robot.")
    else:
        print("✅ Servo đang BẬT.")

    if run_mode == 0:
        print("⚠️ Robot đang ở chế độ IDLE.")
    elif run_mode == 1:
        print("✅ Chế độ MANUAL RUN — có thể điều khiển.")
    elif run_mode == 2:
        print("✅ Chế độ AUTO RUN — đang chạy chương trình.")
    else:
        print(f"⚠️ Chế độ không xác định: run_mode = {run_mode}")

    if err_code != "0":
        print(f"❌ Robot đang báo lỗi hệ thống. Mã lỗi: {err_code}")
    else:
        print("✅ Không có lỗi hệ thống.")

# 🛠️ Gọi khởi động robot
def initialize_robot():
    robot.rm_clear_system_err()                # Xóa lỗi nếu có
    robot.rm_set_arm_run_mode(1)               # Đặt về chế độ điều khiển tay
    robot.rm_set_arm_power(True)               # Bật servo
    print("🔄 Đang chuẩn bị robot...")
    check_robot_ready()                        # Kiểm tra lại toàn bộ sau khi bật

# 🧪 Gọi lệnh khởi động
initialize_robot()

# 🔩 Lấy vị trí hiện tại các khớp
status = robot.rm_get_current_arm_state()
if status[0] == 0:
    joint_angles = status[1]['joint']
    tcp_pose = status[1]['pose']
    error_flags = status[1]['err']

    print("\n🔩 Joint Angles (degrees):", joint_angles)
    print("📍 TCP Pose (x, y, z, rx, ry, rz):", tcp_pose)
else:
    print("❌ Failed to get arm status. Error code:", status[0])

info = robot.rm_get_arm_software_info()
print(info[1]['ctrl_info']['version'])

def get_current_joint_position():
    status = robot.rm_get_current_arm_state()
    if status[0] == 0:
        return status[1]['joint']
    else:
        print(f"❌ Lỗi khi lấy trạng thái khớp. Mã lỗi: {status[0]}")
        return None
import time

def get_tcp_pose():
    status = robot.rm_get_current_arm_state()
    return status[1]["pose"] if status[0] == 0 else None

def move_curve(pose_via, pose_to, v=30, r=0, loop=1, connect=0, block=1):
    try:
        status = robot.rm_movec(pose_via, pose_to, v, r, loop, connect, block)
        if status == 0:
            print("✅ Di chuyển cung tròn từ điểm A → B xong.")
        else:
            print(f"❌ Di chuyển lỗi: {status}")
    except Exception as e:
        print(f"❌ Lỗi khi gọi rm_movec: {e}")

poses = []
print("🔧 Di chuyển robot bằng tay và nhấn Enter sau mỗi điểm. Gõ 'start' để chạy cung tròn, 'exit' để thoát.")

while True:
    cmd = input("⏎ Nhấn Enter để lưu điểm, hoặc gõ 'start' / 'exit': ").strip().lower()

    if cmd == "":
        pose = get_tcp_pose()
        if pose:
            poses.append(pose)
            print(f"✅ Đã lưu điểm {len(poses)}: {[round(p, 4) for p in pose]}")
        else:
            print("❌ Không lấy được pose từ robot.")
    elif cmd == "start":
        print("\n🚀 Bắt đầu chạy từng đoạn cong giữa các điểm đã lưu...")
        if len(poses) < 3:
            print("⚠️ Cần ít nhất 3 điểm để tạo cung tròn (trung gian + đích)!")
            continue

        for i in range(len(poses) - 2):
            via = poses[i+1]
            to  = poses[i+2]
            print(f"▶️ Di chuyển cung tròn từ điểm {i+1} → {i+3} qua điểm giữa {i+2}")
            move_curve(via, to, v=30, r=0, loop=1)
        print("🎯 Đã hoàn tất các đoạn cong.")
    elif cmd == "exit":
        print("🔚 Kết thúc chương trình.")
        break
    else:
        print("⚠️ Lệnh không hợp lệ. Chỉ nhận Enter, 'start' hoặc 'exit'.")

