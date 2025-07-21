import time
import tkinter as tk
from tkinter import messagebox
from Robotic_Arm.rm_robot_interface import *
from modbus import PLCStation

# ⚙️ Khởi tạo
robot = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
handle = robot.rm_create_robot_arm("192.168.1.18", 8080)
print("robotic arm ID:", handle.id)

is_sumilation = True  # Biến toàn cục để xác định có chạy mô phỏng hay không

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

plc = PLCStation(serial_port="COM5", baudrate=9600, timeout=1)
 
# 📦 Lưu điểm
point_list = []

def get_tcp_pose():
    state = robot.rm_get_current_arm_state()
    return state[1]["pose"] if state[0] == 0 else None

def save_point():
    pose = get_tcp_pose()
    if not pose:
        messagebox.showerror("Lỗi", "Không lấy được pose từ robot.")
        return

    plc_choice = plc_var.get()
    move_type = move_var.get()

    plc_outputs = {
        "Bit 0": [True, False, False, False, False],
        "Bit 1": [False, True, False, False, False],
        "Bit 2": [False, False, True, False, False],
        "Tắt":   [False, False, False, False, False]
    }
    plc_out = plc_outputs.get(plc_choice, [False] * 5)

    point_list.append({
        "pose": pose,
        "plc_output": plc_out,
        "move_type": move_type
    })

    listbox.insert(tk.END, f"Điểm {len(point_list)} - {move_type} - {plc_choice}")

def run_sequence():
    for i, pt in enumerate(point_list):
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(i)
        pose = pt["pose"]
        move_type = pt["move_type"]

        # Chọn loại chuyển động
        if move_type == "Đi khớp (movej_p)":
            robot.rm_movej_p(pose, v=10, r=0, connect=0, block=1)
        elif move_type == "Đi tuyến tính (movel)":
            robot.rm_movel(pose, v=10, r=0, connect=0, block=1)
        elif move_type == "Đi spline (moves)":
            robot.rm_moves(pose, v=10, r=0, connect=0, block=1)
        # elif move_type == "Đi cung tròn (movec)":
        #     # Với movec cần 2 điểm: trung gian và đích. Ta dùng cùng 1 điểm giả lập.
        #     robot.rm_movec(pose, pose, v=10, r=0, loop=1, connect=0, block=1)
        else:
            print(f"❌ Không xác định loại di chuyển: {move_type}")
            continue
        
        if is_sumilation:
            plc.write_datas_output(254, [False, False, False, False, False])
        else:
            plc.write_datas_output(254, pt["plc_output"])

        root.update()
        time.sleep(0.5)

    messagebox.showinfo("Hoàn tất", "Robot đã chạy hết chương trình.")

# 🖼️ Giao diện Tkinter
root = tk.Tk()
root.title("Điều khiển Robot + PLC")

frame = tk.Frame(root)
frame.pack(padx=20, pady=10)

# ⚙️ PLC nút bấm
plc_var = tk.StringVar(value="Tắt") 
tk.Label(frame, text="Chọn trạng thái PLC khi lưu điểm:").pack(anchor='w')
plc_frame = tk.Frame(frame)
plc_frame.pack(pady=5)

def toggle_welding():
    if plc_var.get() == "Bit 0":
        plc_var.set("Tắt")
        btn_welding_toggle.config(text="⛔ Tắt hàn")
    else:
        plc_var.set("Bit 0")
        btn_welding_toggle.config(text="🔌 Bật hàn")

btn_welding_toggle = tk.Button(plc_frame, text="⛔ Tắt hàn", width=20,
                                command=toggle_welding)
btn_welding_toggle.pack(side='left', padx=5)

def set_simulation():
    global is_sumilation
    is_sumilation = not is_sumilation
    if is_sumilation:
        btn_move_simulation.config(text="Chạy mô phỏng")
    else:
        btn_move_simulation.config(text="Chạy thực tế")

btn_move_simulation = tk.Button(plc_frame, text="Chạy mô phỏng", width=20,
                                command=set_simulation)
btn_move_simulation.pack(side='left', padx=5)

# ⚙️ Di chuyển robot
move_var = tk.StringVar(value="Đi tuyến tính (movel)")
tk.Label(frame, text="Chọn kiểu di chuyển robot:").pack(anchor='w')
move_frame = tk.Frame(frame)
move_frame.pack(pady=5)

def auto_save_and_reset(move_type):
    move_var.set(move_type)
    save_point()
    reset_buttons()

movej_btn = tk.Button(move_frame, text="🔧 Đi khớp (movej_p)", width=20,
                      command=lambda: auto_save_and_reset("Đi khớp (movej_p)"))
movej_btn.pack(side='left', padx=5)

movel_btn = tk.Button(move_frame, text="📐 Đi tuyến tính (movel)", width=20,
                      command=lambda: auto_save_and_reset("Đi tuyến tính (movel)"))
movel_btn.pack(side='left', padx=5)

# 🔧 Các nút chức năng chính
def reset_buttons():
    movej_btn.config(state='normal', bg="SystemButtonFace")
    movel_btn.config(state='normal', bg="SystemButtonFace")

tk.Button(frame, text="▶️ Chạy tuần tự", command=run_sequence).pack(pady=5)

listbox = tk.Listbox(root, width=60, height=10)
listbox.pack(pady=10)

def reset_all():
    point_list.clear()
    listbox.delete(0, tk.END)
    reset_buttons()

tk.Button(root, text="🔄 Xóa tất cả & bắt đầu lại", command=reset_all).pack(pady=5)

root.mainloop()