# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 22:02:15 2025

@author: DELL
"""

import sys
import os
import cv2
import torch
import pydicom
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                            QStatusBar, QProgressDialog, QTextEdit, QGraphicsView, 
                            QGraphicsScene, QGraphicsPixmapItem)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPainter,QKeyEvent, QWheelEvent,QBrush,QColor
from PyQt5.QtCore import Qt, QPointF,QLineF
import jiance
class MedicalGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.zoom_factor = 1.0
        self.dragging = False
        self.last_mouse_pos = QPointF()
        self.setDragMode(QGraphicsView.NoDrag)  # 禁用默认拖拽模式
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.background_pixmap = QPixmap("med1.png")

        self.background_item = None
        #self.setBackgroundBrush(QBrush(QColor("#1E1E1E")))  # 备用背景色
        #self.setCacheMode(QGraphicsView.CacheBackground)  # 提升渲染性能
    
    def set_background(self, visible=True):
        """动态创建背景项，避免保留已删除的引用"""
        # 先清除旧背景
        for item in self.scene().items():
            if isinstance(item, QGraphicsPixmapItem) and item.zValue() == -1:
                self.scene().removeItem(item)

        if visible and not self.background_pixmap.isNull():
            # 每次创建新对象
            self.background_item = QGraphicsPixmapItem(self.background_pixmap)
            self.background_item.setZValue(-1)
            self.scene().addItem(self.background_item)
            self.fit_background()
   

    def fit_background(self):
        if self.scene() and not self.background_pixmap.isNull():
            # 动态获取当前背景项
            bg_items = [item for item in self.scene().items()
                        if isinstance(item, QGraphicsPixmapItem) 
                        and item.zValue() == -1]
            if bg_items:
                self.fitInView(bg_items[0], Qt.KeepAspectRatioByExpanding)

    def resizeEvent(self, event):
        """窗口大小变化时调整背景"""
        super().resizeEvent(event)
        self.fit_background()
    
        
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 记录初始位置并切换光标
            self.dragging = True
            self.last_mouse_pos = self.mapToScene(event.pos())
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if self.dragging:
            # 计算位移并更新视图
            delta = self.mapToScene(event.pos()) - self.last_mouse_pos
            self.last_mouse_pos = self.mapToScene(event.pos())
            
            # 调整视图中心保持平滑移动
            new_center = self.get_center() - delta
            self.centerOn(new_center)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def get_center(self):
        """获取当前视图中心点"""
        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        return visible_rect.center()
    
    def wheelEvent(self, event: QWheelEvent):
        # 缩放控制
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            factor = zoom_in_factor
            self.zoom_factor *= zoom_in_factor
        else:
            factor = zoom_out_factor
            self.zoom_factor *= zoom_out_factor
        
        self.scale(factor, factor)
        self.centerOn(self.mapToScene(event.pos()))
   
    def start_measuring(self):
        # 实现测量线绘制
        self.measure_start_point = self.mapToScene(self.last_mouse_pos)
        self.measure_line = self.scene().addLine(QLineF())    
    
class MedicalVisionApp(QMainWindow):
    def __init__(self):
            super().__init__()
            self.model = None
            self.current_image = None
            self.dicom_metadata = {}
            self.initUI()
            self.load_model()
            self.batch_images = []      # 存储批量处理结果
            self.current_batch_index = 0 # 当前显示索引
            self.file_path=''
            self.fig_type=0
            self.graphics_view.set_background()  # 初始化时显示背景
            
    def display_image(self, img):
        """更新后的图像显示方法"""
        self.graphics_view.set_background(False)  # 隐藏背景
        
        # 原有图像处理逻辑...
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        # 更新图形项
        self.graphics_scene.clear()
        self.image_item = self.graphics_scene.addPixmap(pixmap)
        self.graphics_view.fitInView(self.image_item, Qt.KeepAspectRatio)
        self.graphics_view.zoom_factor = 1.0

    def clear_display(self):
        """清空显示时恢复背景"""
        self.graphics_scene.clear()
        self.graphics_view.set_background(True)

    def initUI(self):
        # 配置医疗专业主题
        self.set_medical_style()
        
        # 主窗口设置
        self.setWindowTitle("X-ray骨折智能检测系统")
        self.setMinimumSize(1280, 800)
        self.setWindowIcon(QIcon("med.png"))

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 左侧控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(20, 40, 20, 40)
        control_layout.setSpacing(25)

        # 单张操作按钮
        self.upload_btn = QPushButton("上传单张影像")
        self.upload_btn.clicked.connect(self.open_image)
        self.upload_btn.setObjectName("actionButton")

        self.analyze_btn = QPushButton("执行骨折检测")
        self.analyze_btn.clicked.connect(self.analyze_single_image)
        self.analyze_btn.setObjectName("actionButton")

        # 批量操作按钮
        self.batch_btn = QPushButton("批量检测")
        self.batch_btn.clicked.connect(self.batch_process)
        self.batch_btn.setObjectName("actionButton")

        # 导航控制
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        self.prev_btn = QPushButton("← 上一张")
        self.prev_btn.clicked.connect(self.show_prev_image)
        self.next_btn = QPushButton("下一张 →")
        self.next_btn.clicked.connect(self.show_next_image)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)

        # 状态显示
        self.batch_status = QLabel("当前: 0/0")
        self.batch_status.setAlignment(Qt.AlignCenter)
        
        self.upload_dicom_btn = QPushButton("上传DICOM影像")
        self.upload_dicom_btn.clicked.connect(self.open_dicom)
        self.upload_dicom_btn.setObjectName("actionButton")

        # 元数据显示区域
        self.metadata_display = QTextEdit()
        self.metadata_display.setReadOnly(True)
        self.metadata_display.setMaximumHeight(200)
        self.metadata_display.setStyleSheet("""
            QTextEdit {
                background-color: #252526;
                color: #D4D4D4;
                border: 1px solid #3A3A3A;
                font-family: Consolas;
                font-size: 10pt;
            }
        """)

        # 添加到控制面板
        control_layout.addWidget(self.upload_btn)
        control_layout.addWidget(self.upload_dicom_btn)
        control_layout.addWidget(self.analyze_btn)
        control_layout.addWidget(self.batch_btn)
        control_layout.addWidget(nav_widget)
        control_layout.addWidget(self.batch_status)
        control_layout.addWidget(self.metadata_display)  # 新增元数据显示
        control_layout.addStretch()

        # 重构图像显示区域
        self.graphics_view = MedicalGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.image_item = QGraphicsPixmapItem()
        self.graphics_scene.addItem(self.image_item)

        main_layout.addWidget(control_panel, stretch=1)
        main_layout.addWidget(self.graphics_view, stretch=4)


        # 图像显示区域
        '''
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #1E1E1E; border: 2px solid #3A3A3A;")

        main_layout.addWidget(control_panel, stretch=1)
        main_layout.addWidget(self.image_label, stretch=4)
        '''

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def set_medical_style(self):
        # 专业医疗配色方案
        style = """
        QMainWindow {
            background-color: #2D2D30;
        }
        QPushButton#actionButton {
            background-color: #005B96;
            color: #FFFFFF;
            border: none;
            padding: 12px 24px;
            font-size: 14px;
            border-radius: 4px;
            min-width: 120px;
        }
        QPushButton#actionButton:hover {
            background-color: #007CBA;
        }
        QLabel {
            color: #D4D4D4;
            font-family: 'Segoe UI';
        }
        """
        self.setStyleSheet(style)
        
    def open_dicom(self):
        """处理DICOM文件上传"""
        options = QFileDialog.Options()
        self.file_path, _ = QFileDialog.getOpenFileName(
            self, "选择DICOM文件", "", 
            "DICOM文件 (*.dcm)", options=options
        )
        
        if self.file_path:
            try:
                # 读取DICOM文件
                ds = pydicom.dcmread(self.file_path)
                self.dicom_metadata = self.extract_dicom_metadata(ds)
                
                # 转换像素数据
                img_array = self.convert_dicom_to_array(ds)
                self.current_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                # 显示元数据
                self.show_metadata()
                self.display_image(self.current_image)
                self.fig_type=1
                
            except Exception as e:
                self.status_bar.showMessage(f"DICOM文件读取失败: {str(e)}")

    def extract_dicom_metadata(self, dataset):
        """提取关键DICOM元数据"""
        return {
            'Patient Name': str(getattr(dataset, 'PatientName', 'N/A')),
            'Patient ID': str(getattr(dataset, 'PatientID', 'N/A')),
            'Study Date': str(getattr(dataset, 'StudyDate', 'N/A')),
            'Modality': str(getattr(dataset, 'Modality', 'N/A')),
            'Body Part': str(getattr(dataset, 'BodyPartExamined', 'N/A')),
            'Slice Thickness': str(getattr(dataset, 'SliceThickness', 'N/A')) + ' mm',
            'Window Center': str(getattr(dataset, 'WindowCenter', 'N/A')),
            'Window Width': str(getattr(dataset, 'WindowWidth', 'N/A'))
        }

    def convert_dicom_to_array(self, dataset):
        """将DICOM像素数据转换为numpy数组"""
        img = dataset.pixel_array.astype(float)
        
        # 应用窗宽窗位
        center = int(dataset.WindowCenter) if 'WindowCenter' in dataset else img.mean()
        width = int(dataset.WindowWidth) if 'WindowWidth' in dataset else img.max() - img.min()
        
        img = (img - (center - width/2)) / width
        img = np.clip(img, 0, 1)
        img = (img * 255).astype(np.uint8)
        
        # 转换为RGB
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        return img

    def show_metadata(self):
        """显示DICOM元数据"""
        metadata_str = "=== 患者信息 ===\n"
        for key, value in self.dicom_metadata.items():
            metadata_str += f"{key}: {value}\n"
        self.metadata_display.setText(metadata_str)
        
    '''
    def display_image(self, img):
        """重构后的图像显示方法"""
        # 转换颜色空间
        if len(img.shape) == 3 and img.shape[2] == 3:  # BGR格式
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:  # DICOM转换后的RGB格式
            img_rgb = img
        
        # 转换为Qt图像
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        # 更新图形项
        self.graphics_scene.clear()
        self.image_item = self.graphics_scene.addPixmap(pixmap)
        self.graphics_view.fitInView(self.image_item, Qt.KeepAspectRatio)
        self.graphics_view.zoom_factor = 1.0
    '''
    def reset_view(self):
        """重置视图缩放"""
        self.graphics_view.resetTransform()
        self.graphics_view.fitInView(self.image_item, Qt.KeepAspectRatio)
        self.graphics_view.zoom_factor = 1.0
        

    def load_model(self):
        try:
            self.model = torch.load('best.pt')
            self.status_bar.showMessage("模型加载成功", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"模型加载失败: {str(e)}")
            
    def keyPressEvent(self, event: QKeyEvent):
        """键盘左右键控制导航"""
        if event.key() == Qt.Key_Left:
            self.show_prev_image()
        elif event.key() == Qt.Key_Right:
            self.show_next_image()

    def update_navigation(self):
        """更新导航状态显示"""
        self.batch_status.setText(
            f"当前: {self.current_batch_index+1}/{len(self.batch_images)}"
        )
        self.prev_btn.setEnabled(self.current_batch_index > 0)
        self.next_btn.setEnabled(self.current_batch_index < len(self.batch_images)-1)

    def show_prev_image(self):
        if self.current_batch_index > 0:
            self.current_batch_index -= 1
            self.display_batch_image()

    def show_next_image(self):
        if self.current_batch_index < len(self.batch_images)-1:
            self.current_batch_index += 1
            self.display_batch_image()

    def display_batch_image(self):
        """显示批量处理中的当前图像"""
        if self.batch_images:
            img = self.batch_images[self.current_batch_index]
            self.display_image(img)
            self.update_navigation()

    def batch_process(self):
        """批量处理整个文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择医学影像文件夹")
        if not folder:
            return

        # 获取所有支持的图像文件
        valid_ext = ['.jpg', '.jpeg', '.png']
        image_files = [
            os.path.join(folder, f) for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in valid_ext
        ]

        if not image_files:
            self.status_bar.showMessage("文件夹中没有支持的图像文件")
            return

        # 创建进度对话框
        self.metadata_display.setText('None')
        progress = QProgressDialog("批量处理中...", "取消", 0, len(image_files), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        # 清空历史数据
        self.batch_images.clear()
        self.current_batch_index = 0

        # 批量处理
        for i, file_path in enumerate(image_files):
            if progress.wasCanceled():
                break

            try:
                # 处理单张图像
                analyzed_img=jiance.run(figtype=0,source=file_path)


                self.batch_images.append(analyzed_img)
                progress.setValue(i+1)
            except Exception as e:
                print(f"处理失败: {file_path} - {str(e)}")

        progress.close()
        if self.batch_images:
            self.display_batch_image()
            self.status_bar.showMessage(f"完成批量处理，共处理{len(self.batch_images)}张影像")
        else:
            self.status_bar.showMessage("批量处理未获得有效结果")


    def open_image(self):
        self.batch_images.clear()
        self.fig_type=0
        self.metadata_display.setText('None')
        self.current_batch_index = 0
        options = QFileDialog.Options()
        self.file_path, _ = QFileDialog.getOpenFileName(
            self, "选择医学影像", "", 
            "图像文件 (*.jpg *.jpeg *.png)", options=options
        )
        
        if self.file_path:
            self.current_image = cv2.imread(self.file_path)
            self.display_image(self.current_image)
            
    def analyze_single_image(self):
        """单张图像分析（原有analyze_image改名）"""
        if self.current_image is None:
            self.status_bar.showMessage("请先上传医学影像")
            return

        # 清空批量数据
        self.batch_images.clear()
        self.current_batch_index = 0
        analyzed_image=jiance.run(figtype=self.fig_type,source=self.file_path)
        '''


        results = self.model(self.current_image)
        detections = results.pandas().xyxy[0]

        # 绘制检测结果
        analyzed_image = self.current_image.copy()
        for _, row in detections.iterrows():
            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            
            # 绘制医疗绿色方框 (BGR格式)
            cv2.rectangle(analyzed_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 添加标签
            label = f"{row['name']} {row['confidence']:.2f}"
            cv2.putText(analyzed_image, label, (x1, y1-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        '''

        self.display_image(analyzed_image)
        self.reset_view()


    def resizeEvent(self, event):
        if self.current_image is not None:
            self.display_image(self.current_image)
            self.reset_view()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MedicalVisionApp()
    window.show()
    # 窗宽窗位调节滑块

    sys.exit(app.exec_())