import tkinter as tk
from tkinter import ttk
import psutil
import threading
import time
import pystray
from PIL import Image, ImageDraw, ImageTk
import os
import sys

class USBFloatingIcon:
    def __init__(self):
        self.root = tk.Tk()
        
        # 关键：在设置窗口属性前就隐藏
        self.root.withdraw()  # 立即隐藏，不在任务栏显示
        
        self.setup_window()
        self.setup_icon()
        self.usb_detected = False
        self.monitoring = True
        self.tray_icon = None
        
        # 启动系统托盘图标
        self.setup_tray_icon()
        
    def setup_window(self):
        """设置悬浮窗口属性"""
        self.root.overrideredirect(True)  # 无边框窗口
        self.root.attributes('-alpha', 0.4)  # 半透明
        self.root.attributes('-topmost', True)  # 始终置顶
        
        # 设置窗口大小和位置 - 右上角
        self.root.geometry('100x100-200+100')
        
        # 允许窗口拖动
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<ButtonRelease-1>', self.stop_move)
        self.root.bind('<B1-Motion>', self.on_move)
        
    def setup_icon(self):
        """设置悬浮图标"""
        # 创建一个画布来绘制USB图标
        self.canvas = tk.Canvas(self.root, width=100, height=100, 
                               bg='lightblue', highlightthickness=0)
        self.canvas.pack()
        
        # 加载PNG图标或使用备用绘制
        self.load_icon_image()
        
    def get_resource_path(self, filename):
        """获取资源文件的正确路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的路径
            base_path = sys._MEIPASS
        else:
            # 开发时的路径
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, filename)
        
    def load_icon_image(self):
        """加载PNG图标图片"""
        try:
            # 获取图片路径
            image_path = self.get_resource_path('usb_icon.png')
            
            # 加载PNG图片
            pil_image = Image.open(image_path)
            pil_image = pil_image.resize((80, 80), Image.Resampling.LANCZOS)
            
            # 转换为tkinter可用的格式
            self.tk_image = ImageTk.PhotoImage(pil_image)
            
            # 清除画布并显示图片
            self.canvas.delete("all")
            self.canvas.create_image(50, 50, image=self.tk_image)
            
        except Exception as e:
            print(f"加载图片失败: {e}")
            # 如果PNG加载失败，使用绘制的图标
            self.draw_fallback_icon()
    
    def draw_fallback_icon(self):
        """备用方案：绘制图标"""
        self.canvas.delete("all")
        self.canvas.configure(bg='lightblue')
        # 绘制简单的USB图标
        self.canvas.create_rectangle(30, 20, 70, 50, fill='white', outline='black')
        self.canvas.create_rectangle(40, 50, 60, 80, fill='white', outline='black')
        
    def start_move(self, event):
        """开始拖动窗口"""
        self.x = event.x
        self.y = event.y
        
    def stop_move(self, event):
        """停止拖动窗口"""
        self.x = None
        self.y = None
        
    def on_move(self, event):
        """处理窗口拖动"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        
    def check_usb_devices(self):
        """检查USB设备"""
        while self.monitoring:
            usb_found = False
            # 遍历所有磁盘分区
            for partition in psutil.disk_partitions():
                if 'removable' in partition.opts:
                    try:
                        # 尝试访问设备，确认是否可用
                        usage = psutil.disk_usage(partition.mountpoint)
                        usb_found = True
                        break
                    except:
                        continue
            
            # 根据检测结果更新界面
            if usb_found and not self.usb_detected:
                self.usb_detected = True
                self.root.deiconify()  # 显示窗口
                self.update_icon_color('red')  # USB存在时显示红色
            elif not usb_found and self.usb_detected:
                self.usb_detected = False
                self.root.withdraw()  # 隐藏窗口
                
            time.sleep(2)  # 每2秒检查一次
            
    def update_icon_color(self, color):
        """更新图标颜色"""
        self.canvas.config(bg=color)
        # 重绘图标
        self.canvas.delete("all")
        # 重新加载图标（保持红色背景）
        try:
            self.canvas.create_image(50, 50, image=self.tk_image)
        except:
            # 如果图片加载失败，使用绘制的图标
            self.canvas.create_rectangle(30, 20, 70, 50, fill='white', outline='black')
            self.canvas.create_rectangle(40, 50, 60, 80, fill='white', outline='black')
        
    def create_tray_image(self):
        """创建系统托盘图标"""
        # 尝试使用PNG图片
        try:
            image_path = self.get_resource_path('usb_icon.png')
            image = Image.open(image_path)
            image = image.resize((16, 16), Image.Resampling.LANCZOS)
            return image
        except:
            # 如果PNG文件不存在，使用默认图标
            image = Image.new('RGB', (16, 16), 'white')
            dc = ImageDraw.Draw(image)
            dc.rectangle([4, 3, 12, 8], fill='blue')
            dc.rectangle([6, 8, 10, 13], fill='blue')
            return image
        
    def setup_tray_icon(self):
        """设置系统托盘图标和菜单"""
        image = self.create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem('显示/隐藏', self.toggle_visibility),
            pystray.MenuItem('退出', self.quit_app)
        )
        self.tray_icon = pystray.Icon("usb_monitor", image, "别忘记拔U盘", menu)
        
        # 在单独线程中运行系统托盘
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
        
    def toggle_visibility(self, icon, item):
        """切换窗口可见性"""
        if self.root.state() == 'withdrawn':
            self.root.deiconify()
        else:
            self.root.withdraw()
            
    def quit_app(self, icon, item):
        """退出应用程序"""
        self.monitoring = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        os._exit(0)
        
    def run(self):
        """运行应用程序"""
        # 启动USB检测线程
        usb_thread = threading.Thread(target=self.check_usb_devices, daemon=True)
        usb_thread.start()
        
        # 启动主循环
        self.root.mainloop()

if __name__ == "__main__":
    app = USBFloatingIcon()
    app.run()
