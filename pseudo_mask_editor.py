import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class LungMaskEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("模型训练用掩码编辑器 (Mask Editor For Model Training)")
        self.root.minsize(1200, 920)
        
        # 变量初始化
        self.lung_dir = ""
        self.mask_dir = ""
        self.current_lung_img = None
        self.current_mask_img = None
        self.current_display_img = None
        self.current_file = None
        self.file_list = []
        self.current_index = 0
        self.brush_size = 10
        self.draw_mode = "add"  # "add" 或 "remove"
        self.last_x = None
        self.last_y = None
        self.scale_factor = 1.0
        self.is_drawing = False
        
        # 撤销历史
        self.history = []
        self.max_history = 20  # 最多保存的历史步骤数
        
        # 鼠标光标相关变量
        self.cursor_id = None
        
        # 创建UI
        self.create_ui()
        
        # 绑定键盘快捷键
        self.root.bind("<Key>", self.key_pressed)
    
    def create_ui(self):
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧控制面板
        control_frame = tk.Frame(main_frame, width=260, bg="#f0f0f0", padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        control_frame.pack_propagate(False)  # 禁止自动调整大小以保持宽度固定
        
        # 选择文件夹按钮和路径显示
        lung_frame = tk.Frame(control_frame)
        lung_frame.pack(fill=tk.X, pady=5)
        self.lung_btn = tk.Button(lung_frame, text="选择图片文件夹", command=self.select_lung_dir)
        self.lung_btn.pack(fill=tk.X)
        self.lung_path_label = tk.Label(lung_frame, text="", wraplength=180, fg="blue", bg="#f0f0f0", justify=tk.LEFT)
        self.lung_path_label.pack(fill=tk.X)
        
        mask_frame = tk.Frame(control_frame)
        mask_frame.pack(fill=tk.X, pady=5)
        self.mask_btn = tk.Button(mask_frame, text="选择掩码文件夹", command=self.select_mask_dir)
        self.mask_btn.pack(fill=tk.X)
        self.mask_path_label = tk.Label(mask_frame, text="", wraplength=180, fg="blue", bg="#f0f0f0", justify=tk.LEFT)
        self.mask_path_label.pack(fill=tk.X)
        
        # 文件导航
        nav_frame = tk.Frame(control_frame)
        nav_frame.pack(fill=tk.X, pady=10)
        tk.Button(nav_frame, text="<<", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text=">>", command=self.next_image).pack(side=tk.RIGHT, padx=5)
        
        # 当前文件显示
        self.file_label = tk.Label(control_frame, text="未选择文件", wraplength=180)
        self.file_label.pack(fill=tk.X, pady=5)
        
        # 显示进度
        self.progress_label = tk.Label(control_frame, text="0/0")
        self.progress_label.pack(fill=tk.X, pady=5)
        
        # 绘制模式
        mode_frame = tk.LabelFrame(control_frame, text="绘制模式", padx=5, pady=5)
        mode_frame.pack(fill=tk.X, pady=10)
        
        self.mode_var = tk.StringVar(value="add")
        tk.Radiobutton(mode_frame, text="添加区域(前景)", variable=self.mode_var, value="add", 
                    command=self.update_mode).pack(anchor=tk.W)
        tk.Radiobutton(mode_frame, text="删除区域(背景)", variable=self.mode_var, value="remove", 
                    command=self.update_mode).pack(anchor=tk.W)
        
        # 笔刷大小
        brush_frame = tk.LabelFrame(control_frame, text="笔刷大小", padx=5, pady=5)
        brush_frame.pack(fill=tk.X, pady=10)
        
        self.brush_scale = tk.Scale(brush_frame, from_=1, to=50, orient=tk.HORIZONTAL, 
                                command=self.update_brush_size)
        self.brush_scale.set(10)
        self.brush_scale.pack(fill=tk.X)
        
        # 添加撤销按钮
        tk.Button(control_frame, text="撤销(Ctrl+Z)", command=self.undo_last_action, bg="#FF9800", fg="white").pack(fill=tk.X, pady=5)
        
        # 保存按钮
        tk.Button(control_frame, text="保存当前掩码", command=self.save_mask, bg="#4CAF50", fg="white").pack(fill=tk.X, pady=10)
        
        # 说明文本
        instruction_text = (
            "操作说明:\n"
            "- 左键拖动: 绘制\n"
            "- A: 添加模式\n"
            "- R: 删除模式\n"
            "- +/-: 调整笔刷大小\n"
            "- S: 保存当前掩码\n"
            "- Ctrl+Z: 撤销\n"
            "- Ctrl+Shift+Z: 重做\n"
            "- 左右方向键: 切换图片"
        )
        tk.Label(control_frame, text=instruction_text, justify=tk.LEFT, bg="#f0f0f0", 
                wraplength=180).pack(fill=tk.X, pady=5)

        # 保存成功提示（初始化为空）
        self.save_status_label = tk.Label(control_frame, text="", fg="green", bg="#f0f0f0", font=("Arial", 12), wraplength=170)
        self.save_status_label.pack(fill=tk.X, pady=5)

        # 添加作者信息和链接
        author_frame = tk.Frame(control_frame, bg="#f0f0f0")
        author_frame.pack(side=tk.BOTTOM, pady=5, fill=tk.X)

        # 邮件链接
        email_label = tk.Label(author_frame, text="© 2025 Zhiqian Yu | Email Me", fg="blue", bg="#f0f0f0", font=("Arial", 10), cursor="hand2")
        email_label.pack(side=tk.LEFT, padx=5)
        email_label.bind("<Button-1>", lambda e: os.system(f'start mailto:yu-zhiqian@outlook.com'))

        # GitHub链接
        github_label = tk.Label(author_frame, text="GitHub", fg="blue", bg="#f0f0f0", font=("Arial", 10), cursor="hand2")
        github_label.pack(side=tk.RIGHT, padx=5)
        github_label.bind("<Button-1>", lambda e: os.system('start https://github.com/zhiqianyu'))
            
        # 图像显示区域
        self.canvas_frame = tk.Frame(main_frame, bg="black")
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 画布事件绑定
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        self.canvas.bind("<Configure>", self.resize_canvas)
        self.canvas.bind("<Motion>", self.update_cursor)
        self.canvas.bind("<Leave>", self.remove_cursor)
    
    def select_lung_dir(self):
        self.lung_dir = filedialog.askdirectory(title="选择原图像文件夹")
        if self.lung_dir:
            # 获取并设置相对路径显示
            self.lung_path_label.config(text=self.get_display_path(self.lung_dir))
            
            if self.lung_dir and self.mask_dir:
                self.load_file_list()

    def select_mask_dir(self):
        self.mask_dir = filedialog.askdirectory(title="选择掩码图像文件夹")
        if self.mask_dir:
            # 获取并设置相对路径显示
            self.mask_path_label.config(text=self.get_display_path(self.mask_dir))
            
            if self.lung_dir and self.mask_dir:
                self.load_file_list()
    
    def get_display_path(self, path):
        """获取路径的相对表示形式"""
        # 获取路径的最后几级目录
        path_parts = path.split(os.sep)
        # 过滤掉空字符串
        path_parts = [p for p in path_parts if p]
        
        # 如果路径很长，只显示最后3级目录
        if len(path_parts) > 3:
            return ".../" + os.sep.join(path_parts[-3:])
        else:
            return path
    
    def load_file_list(self):
        # 获取lung文件夹下的所有文件
        lung_files = [f for f in os.listdir(self.lung_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        
        # 获取mask文件夹下的所有文件
        mask_files_with_suffix = [f for f in os.listdir(self.mask_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        
        # 处理文件名映射
        mask_to_lung_map = {}
        for mask_file in mask_files_with_suffix:
            # 尝试移除"_mask"后缀
            base_name = mask_file
            if "_mask" in mask_file:
                # 找到文件扩展名
                file_name, file_ext = os.path.splitext(mask_file)
                # 移除"_mask"后缀
                base_name = file_name.replace("_mask", "") + file_ext
            
            # 映射文件名，无论是否有"_mask"后缀
            mask_to_lung_map[base_name] = mask_file
            mask_to_lung_map[mask_file] = mask_file  # 直接映射原始文件名
        
        # 找出lung文件夹中存在对应mask的文件
        common_files = [f for f in lung_files if f in mask_to_lung_map]
        
        if not common_files:
            messagebox.showwarning("警告", "未找到匹配的lung和mask文件！\n注意：掩码文件应比原图多'_mask'后缀或与原图文件名相同")
            return
            
        # 保存文件名映射关系，用于加载mask
        self.mask_name_map = mask_to_lung_map
        
        self.file_list = sorted(list(common_files))
        self.current_index = 0
        self.load_current_image()
        
        # 更新进度显示
        self.update_progress_label()
    
    def load_current_image(self):
        if not self.file_list:
            return
        
        self.current_file = self.file_list[self.current_index]
        
        # 加载lung图像
        lung_path = os.path.join(self.lung_dir, self.current_file)
        self.current_lung_img = cv2.imread(lung_path)
        
        # 如果是灰度图，转换为RGB
        if len(self.current_lung_img.shape) == 2:
            self.current_lung_img = cv2.cvtColor(self.current_lung_img, cv2.COLOR_GRAY2BGR)
        elif self.current_lung_img.shape[2] == 1:
            self.current_lung_img = cv2.cvtColor(self.current_lung_img, cv2.COLOR_GRAY2BGR)
        
        # 加载mask图像 - 使用映射的文件名
        mask_filename = self.mask_name_map.get(self.current_file, self.current_file)
        mask_path = os.path.join(self.mask_dir, mask_filename)
        self.current_mask_img = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        
        # 清除历史记录
        self.history = []
        
        # 保存初始状态到历史记录
        self.save_to_history()
        
        # 创建用于显示的图像 - 将mask边缘绘制到原图上
        self.update_display_image()
        
        # 更新文件名显示
        self.file_label.config(text=f"当前文件: {self.current_file}")
        self.update_progress_label()
    
    def update_display_image(self):
        if self.current_lung_img is None or self.current_mask_img is None:
            return
        
        # 创建显示图像的副本
        self.current_display_img = self.current_lung_img.copy()
        
        # 找到mask的轮廓
        contours, _ = cv2.findContours(self.current_mask_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 在lung图像上绘制mask轮廓
        cv2.drawContours(self.current_display_img, contours, -1, (0, 255, 0), 2)
        
        # 显示图像
        self.show_image()
    
    def show_image(self):
        if self.current_display_img is None:
            return
        
        # 计算缩放比例，使图像适应canvas大小
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas尚未初始化完成，稍后重试
            self.root.after(100, self.show_image)
            return
        
        img_height, img_width = self.current_display_img.shape[:2]
        
        # 计算适合canvas的缩放比例
        width_ratio = canvas_width / img_width
        height_ratio = canvas_height / img_height
        self.scale_factor = min(width_ratio, height_ratio) * 0.9  # 留一些边距
        
        # 缩放图像
        new_width = int(img_width * self.scale_factor)
        new_height = int(img_height * self.scale_factor)
        
        # 转换为PIL格式
        display_img = cv2.cvtColor(self.current_display_img, cv2.COLOR_BGR2RGB)
        display_img = cv2.resize(display_img, (new_width, new_height))
        display_img = Image.fromarray(display_img)
        
        # 转换为PhotoImage
        self.tk_image = ImageTk.PhotoImage(image=display_img)
        
        # 清除画布并显示新图像
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width/2, canvas_height/2, 
            image=self.tk_image, 
            anchor=tk.CENTER,
            tags="image"
        )
    
    def resize_canvas(self, event):
        # 窗口大小改变时重新显示图像
        if self.current_display_img is not None:
            self.show_image()
    
    def update_mode(self):
        self.draw_mode = self.mode_var.get()
    
    def update_brush_size(self, value):
        self.brush_size = int(float(value))
        # 更新光标大小
        if self.last_x is not None and self.last_y is not None:
            self.update_cursor(None)
    
    def start_draw(self, event):
        if self.current_mask_img is None:
            return
            
        # 保存当前状态到历史记录
        self.save_to_history()
        
        self.is_drawing = True
        self.last_x = event.x
        self.last_y = event.y
        
        # 在绘制开始时就更新鼠标位置
        self.update_cursor_position(event.x, event.y)
        
        self.draw(event)

    def draw(self, event):
        if not self.is_drawing or self.current_mask_img is None:
            return

        # 获取canvas和图像尺寸
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_height, img_width = self.current_mask_img.shape[:2]

        display_width = int(img_width * self.scale_factor)
        display_height = int(img_height * self.scale_factor)

        offset_x = (canvas_width - display_width) / 2
        offset_y = (canvas_height - display_height) / 2

        # 计算图像坐标
        img_x = int((event.x - offset_x) / self.scale_factor)
        img_y = int((event.y - offset_y) / self.scale_factor)
        last_img_x = int((self.last_x - offset_x) / self.scale_factor)
        last_img_y = int((self.last_y - offset_y) / self.scale_factor)

        if (0 <= img_x < img_width and 0 <= img_y < img_height and
            0 <= last_img_x < img_width and 0 <= last_img_y < img_height):

            if self.draw_mode == "add":
                # 添加白色线条
                cv2.line(self.current_mask_img, (last_img_x, last_img_y), (img_x, img_y), 255, self.brush_size)

                # 自动闭合连接：只保留外部轮廓，移除碎块
                contours, _ = cv2.findContours(self.current_mask_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cleaned_mask = np.zeros_like(self.current_mask_img)
                cv2.drawContours(cleaned_mask, contours, -1, 255, -1)
                self.current_mask_img = cleaned_mask

            else:  # 删除模式
                # 画黑线
                cv2.line(self.current_mask_img, (last_img_x, last_img_y), (img_x, img_y), 0, self.brush_size)

                # 删除小的孤立区域（默认阈值20像素面积）
                # self.current_mask_img = self.remove_small_islands(self.current_mask_img, min_area=20)
                # 保留两个最大区域（即左右肺叶）
                self.current_mask_img = self.remove_non_lung_regions(self.current_mask_img, keep_top=2)

            # 更新显示
            self.update_display_image()

        # 更新上一个坐标
        self.last_x = event.x
        self.last_y = event.y

        # 更新光标
        self.update_cursor_position(event.x, event.y)


    def stop_draw(self, event):
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        
        # 在绘制结束时更新光标位置
        if event:
            self.update_cursor_position(event.x, event.y)
    
    def save_mask(self):
        if self.current_mask_img is None or self.current_file is None:
            messagebox.showwarning("警告", "没有可保存的掩码！")
            return

        # 从当前掩码中重新提取轮廓（只保留外部）
        contours, _ = cv2.findContours(self.current_mask_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 创建一个干净的黑图作为新掩码
        new_mask = np.zeros_like(self.current_mask_img)
        new_mask = self.remove_small_islands(new_mask)
        
        
        # 绘制轮廓为白色前景
        cv2.drawContours(new_mask, contours, -1, color=255, thickness=-1)

        # 保存掩码
        mask_filename = self.mask_name_map.get(self.current_file, self.current_file)
        mask_filename_no_ext = os.path.splitext(mask_filename)[0]
        mask_path = os.path.join(self.mask_dir, mask_filename_no_ext + ".png")
        cv2.imwrite(mask_path, new_mask)

        self.show_save_status(f"已保存:\n{mask_filename_no_ext if len(mask_filename_no_ext) <= 21 else mask_filename_no_ext[:20] + '...'}")\
    
    def remove_small_islands(self, mask, min_area=20):
        # 找到所有白色区域
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cleaned_mask = np.zeros_like(mask)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= min_area:
                cv2.drawContours(cleaned_mask, [cnt], -1, 255, -1)

        return cleaned_mask
    
    def show_save_status(self, message):
        self.save_status_label.config(text=message)
        self.root.after(2000, lambda: self.save_status_label.config(text=""))
    
    def next_image(self):
        if not self.file_list:
            return
        
        if self.current_index < len(self.file_list) - 1:
            self.current_index += 1
            self.load_current_image()
    
    def prev_image(self):
        if not self.file_list:
            return
        
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
    
    def update_cursor(self, event):
        """更新鼠标光标位置"""
        if event is None:
            return
        
        # 记录鼠标位置并更新光标
        self.update_cursor_position(event.x, event.y)

    def update_cursor_position(self, x, y):
        """在指定位置显示光标（十字+圆形）"""
        # 删除旧的光标
        self.remove_cursor(None)
        
        # 计算笔刷实际大小
        brush_size_px = int(self.brush_size * self.scale_factor)
        
        # 创建光标组（圆形+十字线）
        self.cursor_id = []
        
        # 绘制圆形
        circle_id = self.canvas.create_oval(
            x - brush_size_px//2, y - brush_size_px//2,
            x + brush_size_px//2, y + brush_size_px//2,
            outline="yellow", width=2
        )
        self.cursor_id.append(circle_id)
        
        # 添加十字线 - 使用与圆相同的大小
        horizontal_line = self.canvas.create_line(
            x - brush_size_px//2, y, x + brush_size_px//2, y, 
            fill="yellow", width=1
        )
        self.cursor_id.append(horizontal_line)
        
        vertical_line = self.canvas.create_line(
            x, y - brush_size_px//2, x, y + brush_size_px//2, 
            fill="yellow", width=1
        )
        self.cursor_id.append(vertical_line)

    def remove_cursor(self, event):
        """删除光标"""
        if self.cursor_id:
            # 删除所有光标元素
            if isinstance(self.cursor_id, list):
                for item in self.cursor_id:
                    self.canvas.delete(item)
            else:
                self.canvas.delete(self.cursor_id)
            self.cursor_id = None
    
    def key_pressed(self, event):
        key = event.keysym.lower()
        
        # Ctrl+Z 撤销
        if event.state & 4 and key == 'z':  # Ctrl+Z
            self.undo_last_action()
            return
            
        if key == 'a':  # 添加模式
            self.mode_var.set("add")
            self.update_mode()
        elif key == 'r':  # 删除模式
            self.mode_var.set("remove")
            self.update_mode()
        elif key == 'plus' or key == 'equal':  # 增加笔刷大小
            new_size = min(self.brush_size + 2, 50)
            self.brush_scale.set(new_size)
            self.update_brush_size(new_size)
        elif key == 'minus':  # 减小笔刷大小
            new_size = max(self.brush_size - 2, 1)
            self.brush_scale.set(new_size)
            self.update_brush_size(new_size)
        elif key == 's':  # 保存
            self.save_mask()
        elif key == 'Right':  # 下一张图片
            self.next_image()
        elif key == 'Left':  # 上一张图片
            self.prev_image()
    
    def save_to_history(self):
        """保存当前掩码状态到历史记录"""
        if self.current_mask_img is None:
            return
            
        # 创建掩码的副本
        mask_copy = self.current_mask_img.copy()
        
        # 添加到历史记录
        self.history.append(mask_copy)
        
        # 限制历史记录长度，防止内存占用过大
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def undo_last_action(self):
        """撤销上一次操作"""
        if not self.history or len(self.history) <= 1:
            messagebox.showinfo("提示", "没有可撤销的操作！")
            return
        
        # 移除当前状态
        self.history.pop()
        
        # 获取上一个状态
        last_state = self.history[-1].copy()
        
        # 恢复到上一个状态
        self.current_mask_img = last_state
        
        # 更新显示
        self.update_display_image()
    
    def update_progress_label(self):
        if self.file_list:
            self.progress_label.config(text=f"{self.current_index + 1}/{len(self.file_list)}")
        else:
            self.progress_label.config(text="0/0")
    
    def remove_non_lung_regions(self, mask, keep_top=2):
        """
        保留最大的 `keep_top` 个区域，删除其余所有区域。
        通常设置 keep_top=2 保留左右两个肺叶。
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 将轮廓按面积排序（降序）
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

        # 创建新mask，仅保留前 N 大区域
        cleaned_mask = np.zeros_like(mask)
        for cnt in sorted_contours[:keep_top]:
            cv2.drawContours(cleaned_mask, [cnt], -1, 255, -1)

        return cleaned_mask

if __name__ == "__main__":
    __author__ = "Zhiqian Yu"
    __version__ = "1.0.0"
    __email__ = "yu-zhiqian@outlook.com"
    __license__ = "For personal, non-commercial use only. Must cite if used in research. Commercial use requires permission."
    root = tk.Tk()
    app = LungMaskEditor(root)
    root.mainloop()