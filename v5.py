# -*- coding: utf-8 -*-
"""
Created on Tue Sep  2 17:32:21 2025

@author: DELL
"""
import sys  # 导入sys模块
sys.setrecursionlimit(3000)  # 将默认的递归深度修改为3000

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import base64
import httpx
import os
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import sys
import cv2
import torch
import pydicom
import numpy as np
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                            QStatusBar, QProgressDialog, QTextEdit, QGraphicsView, 
                            QGraphicsScene, QGraphicsPixmapItem, QGroupBox, QDialog,
                            QFormLayout, QLineEdit, QTextEdit, QPushButton, QVBoxLayout,
                            QHBoxLayout, QMessageBox,QShortcut)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPainter, QKeyEvent, QWheelEvent, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QPointF, QLineF, QTimer, QPropertyAnimation, QEasingCurve
import jiance
from datetime import datetime
import math
# 在导入部分添加QPainterPath
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPainter, QKeyEvent, QWheelEvent, QBrush, QColor, QFont, QPainterPath,QPen,QKeySequence
# 新增：波浪等待动画控件
# 修改WaveWaitWidget类，增强动画效果
# 在文件顶部添加导入
from PyQt5.QtCore import QPropertyAnimation, QPoint, QRectF, QEasingCurve
# 新增：分析完成动画控件
class AnalysisCompleteWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.animation_stage = 0
        self.checkmark_progress = 0
        self.circle_scale = 0
        self.fade_opacity = 0
        
        # 动画颜色设置
        self.circle_color = QColor(46, 204, 113)  # 成功绿色
        self.checkmark_color = QColor(255, 255, 255)  # 白色
        
        # 设置定时器用于动画
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # 约60fps
        
    def update_animation(self):
        if self.animation_stage == 0:
            # 第一阶段：圆圈缩放
            self.circle_scale += 0.05
            if self.circle_scale >= 1.0:
                self.circle_scale = 1.0
                self.animation_stage = 1
        elif self.animation_stage == 1:
            # 第二阶段：对勾绘制
            self.checkmark_progress += 0.03
            if self.checkmark_progress >= 1.0:
                self.checkmark_progress = 1.0
                self.animation_stage = 2
        elif self.animation_stage == 2:
            # 第三阶段：渐显文字
            self.fade_opacity += 0.02
            if self.fade_opacity >= 1.0:
                self.fade_opacity = 1.0
                self.timer.stop()  # 动画完成，停止定时器
        
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        size = min(self.width(), self.height()) * 0.7
        
        # 绘制背景圆圈（带缩放动画）
        painter.setPen(QPen(self.circle_color, 4))
        painter.setBrush(QBrush(self.circle_color))
        
        circle_rect = QRectF(
            center_x - size/2 * self.circle_scale,
            center_y - size/2 * self.circle_scale,
            size * self.circle_scale,
            size * self.circle_scale
        )
        painter.drawEllipse(circle_rect)
        
        # 绘制对勾（带绘制动画）
        if self.animation_stage >= 1:
            painter.setPen(QPen(self.checkmark_color, 6, Qt.SolidLine, Qt.RoundCap))
            
            checkmark_path = QPainterPath()
            checkmark_path.moveTo(center_x - size/3, center_y)
            checkmark_path.lineTo(center_x - size/10, center_y + size/3)
            checkmark_path.lineTo(center_x + size/2.5, center_y - size/3)
            
            # 创建路径测量用于动画
            path_length = checkmark_path.length()
            draw_length = path_length * self.checkmark_progress
            
            # 绘制动画中的对勾
            drawn_path = QPainterPath()
            for i in range(0, 100):
                percent = i / 100.0
                if percent * path_length <= draw_length:
                    point = checkmark_path.pointAtPercent(percent)
                    if i == 0:
                        drawn_path.moveTo(point)
                    else:
                        drawn_path.lineTo(point)
            
            painter.drawPath(drawn_path)
        
        # 绘制文字（渐显动画）
        if self.animation_stage >= 2:
            painter.setOpacity(self.fade_opacity)
            font = QFont("Microsoft YaHei", 14, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            
            text = "分析完成"
            text_rect = painter.fontMetrics().boundingRect(text)
            painter.drawText(
                center_x - int(text_rect.width()/2),
                center_y + int(size/2) + 30,
                text
            )
class WaveWaitWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.wave_phase = 0
        self.wave_amplitude = 12  # 增加振幅使波浪更明显
        self.wave_frequency = 0.03  # 调整频率
        self.wave_color = QColor(25, 118, 210, 200)
        self.text_color = QColor(50, 50, 50)
        self.background_color = QColor(240, 240, 240, 220)
        
        # 设置定时器用于动画 - 增加刷新频率
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(30)  # 增加到30ms刷新一次（约33fps）
        
    def update_wave(self):
        self.wave_phase += 0.15  # 增加相位变化速度
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制半透明背景
        painter.setBrush(self.background_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        
        # 绘制文字
        font = QFont("Microsoft YaHei", 12)
        painter.setFont(font)
        painter.setPen(self.text_color)
        painter.drawText(self.rect(), Qt.AlignCenter, "骨科智能助手正在分析中...\n\n请稍候，这可能需要10-30秒")
        
        # 绘制多层波浪线 - 创建更丰富的波浪效果
        center_y = self.height() // 2 + 40
        
        # 第一层波浪（主波浪）
        wave_path1 = QPainterPath()
        wave_path1.moveTo(0, center_y)
        
        for x in range(0, self.width() + 5, 4):  # 增加采样密度
            y = center_y + self.wave_amplitude * math.sin(self.wave_frequency * x + self.wave_phase)
            wave_path1.lineTo(x, y)
        
        # 第二层波浪（次级波浪，相位偏移）
        wave_path2 = QPainterPath()
        wave_path2.moveTo(0, center_y)
        
        for x in range(0, self.width() + 5, 4):
            y = center_y + self.wave_amplitude * 0.7 * math.cos(self.wave_frequency * x * 1.5 + self.wave_phase + math.pi/3)
            wave_path2.lineTo(x, y)
        
        # 第三层波浪（小波浪，更高频率）
        wave_path3 = QPainterPath()
        wave_path3.moveTo(0, center_y)
        
        for x in range(0, self.width() + 5, 3):
            y = center_y + self.wave_amplitude * 0.4 * math.sin(self.wave_frequency * x * 2 + self.wave_phase * 1.2 + math.pi/2)
            wave_path3.lineTo(x, y)
        
        # 绘制波浪线
        pen1 = QPen(self.wave_color, 3)
        pen2 = QPen(QColor(65, 150, 250, 160), 2)  # 更亮的蓝色
        pen3 = QPen(QColor(100, 180, 255, 120), 1.5)  # 更浅的蓝色
        
        painter.setPen(pen1)
        painter.drawPath(wave_path1)
        
        painter.setPen(pen2)
        painter.drawPath(wave_path2)
        
        painter.setPen(pen3)
        painter.drawPath(wave_path3)
        
        # 添加动态点效果 - 在波峰上绘制移动的点
        dot_spacing = 50  # 点之间的间距
        for x in range(0, self.width(), dot_spacing):
            dot_x = (x + self.wave_phase * 10) % self.width()  # 让点随着波浪移动
            wave_height = self.wave_amplitude * math.sin(self.wave_frequency * dot_x + self.wave_phase)
            dot_y = center_y + wave_height
            
            # 绘制小圆点
            painter.setBrush(QColor(255, 255, 255, 180))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(dot_x, dot_y), 3, 3)

# 新增：病历预览对话框类
class ReportPreviewDialog(QDialog):
    def __init__(self, parent=None, report_image=None):
        super().__init__(parent)
        self.setWindowTitle("病历报告预览")
        self.setMinimumSize(50, 200)
        self.report_image = report_image
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        # 更新显示的图像
        if self.report_image:
            # 将PIL图像转换为QPixmap
            img_bytes = BytesIO()
            self.report_image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes.getvalue())
            self.image_label.setPixmap(pixmap)
            self.image_label.setScaledContents(True)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存为图片")
        self.save_btn.clicked.connect(self.save_as_image)
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addWidget(self.image_label)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_as_image(self):
        """将病历保存为图片"""
        try:
            if self.report_image:
                # 保存文件极简测试 payload
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "保存病历图片", "", "PNG图片 (*.png);;JPEG图片 (*.jpg)"
                )
                
                if file_path:
                    self.report_image.save(file_path)
                    QMessageBox.information(self, "成功", f"病历已保存为图片: {file_path}")
                    
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存图片时发生错误: {str(e)}")

# 修改MedicalRecordDialog类中的按钮区域
class MedicalRecordDialog(QDialog):
    def __init__(self, parent=None, metadata=None, analysis_result=None):
        super().__init__(parent)
        self.setWindowTitle("患者病历报告")
        self.setMinimumSize(800, 600)
        self.metadata = metadata or {}
        self.analysis_result = analysis_result or ""
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 患者基本信息表单
        info_group = QGroupBox("患者基本信息")
        form_layout = QFormLayout()
        
        self.patient_name = QLineEdit(self.metadata.get('Patient Name', ''))
        self.patient_id = QLineEdit(self.metadata.get('Patient ID', ''))
        self.study_date = QLineEdit(self.metadata.get('Study Date', ''))
        self.modality = QLineEdit(self.metadata.get('Modality', ''))
        self.body_part = QLineEdit(self.metadata.get('Body Part', ''))
        
        form_layout.addRow("姓名:", self.patient_name)
        form_layout.addRow("ID:", self.patient_id)
        form_layout.addRow("检查日期:", self.study_date)
        form_layout.addRow("设备类型:", self.modality)
        form_layout.addRow("检查部位:", self.body_part)
        
        info_group.setLayout(form_layout)
        layout.addWidget(info_group)
        
        # 影像评估
        assessment_group = QGroupBox("影像评估")
        assessment_layout = QVBoxLayout()
        self.assessment_text = QTextEdit()
        self.assessment_text.setPlainText(self.extract_assessment_from_result())
        assessment_layout.addWidget(self.assessment_text)
        assessment_group.setLayout(assessment_layout)
        layout.addWidget(assessment_group)
        
        # 诊断结论
        diagnosis_group = QGroupBox("诊断结论")
        diagnosis_layout = QVBoxLayout()
        self.diagnosis_text = QTextEdit()
        self.diagnosis_text.setPlainText(self.extract_diagnosis_from_result())
        diagnosis_layout.addWidget(self.diagnosis_text)
        diagnosis_group.setLayout(diagnosis_layout)
        layout.addWidget(diagnosis_group)
        
        # 建议
        recommendation_group = QGroupBox("治疗建议")
        recommendation_layout = QVBoxLayout()
        self.recommendation_text = QTextEdit()
        self.recommendation_text.setPlainText(self.extract_recommendation_from_result())
        recommendation_layout.addWidget(self.recommendation_text)
        recommendation_group.setLayout(recommendation_layout)
        layout.addWidget(recommendation_group)
        
        # 按钮区域 - 修改这里：将"保存为图片"改为"查看最终病历"
        button_layout = QHBoxLayout()
        self.preview_btn = QPushButton("查看最终病历")  # 修改按钮文本
        self.preview_btn.clicked.connect(self.preview_report)  # 修改连接的方法
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def preview_report(self):
        """预览最终病历报告"""
        try:
            # 获取美观的病历图片
            img = self.create_beautiful_report()
            
            # 创建并显示预览对话框
            preview_dialog = ReportPreviewDialog(self, img)
            preview_dialog.exec_()
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"生成预览时发生错误: {str(e)}")
    
    def wrap_text_by_char_count(self, text, max_chars):
        """按字符数换行，确保每行最多指定数量的字符"""
        lines = []
        
        # 如果没有文本，返回空列表
        if not text:
            return lines
        
        # 分割段落
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append('')
                continue
                
            # 按字符数分割
            start = 0
            while start < len(paragraph):
                # 找到合适的换行位置
                end = start + max_chars
                if end >= len(paragraph):
                    lines.append(paragraph[start:])
                    break
                    
                # 尽量在标点符号或空格处换行
                #while end > start and paragraph[end] not in ['，', '。', '；', '！', '？', '、', ' ']:
                #    end -= 1
                    
                if end == start:  # 如果没有找到合适的换行点，强制换行
                    end = start + max_chars
                    
                lines.append(paragraph[start:end])
                start = end
                
        return lines        
    # 确保原有的病历布局和设计完全保持不变
    def create_beautiful_report(self):
        """创建美观的病历报告图片"""
        # 原有的实现保持不变
        try:
            # 创建图片尺寸，与参考图片保持一致但增加高度以容纳X光图像
            img_width, img_height = 800, 1600
            img = Image.new('RGB', (img_width, img_height), color=(255, 255, 255))
            
            # 创建绘图对象
            draw = ImageDraw.Draw(img)
            
            # 尝试使用中文字极简测试 payload体
            try:
                title_font = ImageFont.truetype("simhei.ttf", 28)
                header_font = ImageFont.truetype("simhei.ttf", 22)
                text_font = ImageFont.truetype("simhei.ttf", 18)
                small_font = ImageFont.truetype("simhei.ttf", 16)
            except:
                title_font = ImageFont.load_default()
                header_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # 绘制顶部标题栏 - 使用深蓝色
            draw.rectangle([(0, 0), (img_width, 50)], fill=(25, 118, 210), outline=None)
            draw.text((img_width//2, 25), "医疗影像诊断报告", font=title_font, fill='white', anchor='mm')
            
            # 绘制医院信息
            hospital_text = "Xray-AI Medical Center"
            hospital_bbox = draw.textbbox((0, 0), hospital_text, font=small_font)
            hospital_width = hospital_bbox[2] - hospital_bbox[0]
            draw.text((img_width-20, 25), hospital_text, font=small_font, fill='white', anchor='rm')
            
            # 添加医生信息和报告日期
            draw.text((20, 60), "诊断医生: Dr. AI", font=text_font, fill=(0, 0, 0))
            draw.text((20, 85), f"报告日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", font=text_font, fill=(0, 0, 0))
            
            # 绘制分隔线极简测试 payload
            draw.line([(20, 110), (img_width-20, 110)], fill=(200, 200, 200), width=1)
            
            # 绘制患者信息区域
            draw.text((20, 130), "患者基本信息", font=header_font, fill=(25, 118, 210))
            
            # 患者详细信息
            info_lines = [
                f"姓名: {self.patient_name.text()}",
                f"ID: {self.patient_id.text()}",
                f"检查日期: {self.study_date.text()}",
                f"检查部位: {self.body_part.text()}"
            ]
            
            y_pos = 160
            for line in info_lines:
                draw.text((30, y_pos), line, font=text_font, fill=(0, 0, 0))
                y_pos += 25
            
            # 绘制影像评估区域
            draw.text((20, 260), "影像评估", font=header_font, fill=(25, 118, 210))
            
            # 使用AI分析结果中的影像评估内容
            assessment = self.extract_assessment_from_result()
            # 删除所有无效符号
            assessment = assessment.replace('*', '').replace('--', '').replace('**', '').replace('#', '').replace(' -', '')
            
            y_pos = 290
            
            # 处理评估文本，确保不会超出边界
            assessment_lines = assessment.split('\n')
            line_number = 1
            for line in assessment_lines:
                if line.strip():  # 只处理非空行
                    # 检查是否已经有序极简测试 payload号，如果没有则添加
                    if not line.strip()[0].isdigit():
                        line = f"{line}"
                        line_number += 1
                    
                    # 分行绘制，确保每行不超过指定宽度
                    wrapped_lines = self.wrap_text_by_char_count(line, 40)
                    for wrapped_line in wrapped_lines:
                        draw.text((30, y_pos), wrapped_line, font=text_font, fill=(0, 0, 0))
                        y_pos += 20
            
            # 绘制诊断结论区域
            draw.text((20, y_pos+20), "诊断结论", font=header_font, fill=(25, 118, 210))
            
            # 使用AI分析结果中的诊断结论内容
            diagnosis = self.extract_diagnosis_from_result()
            # 删除所有无效符号
            diagnosis = diagnosis.replace('*', '').replace('--', '').replace('**', '').replace('#', '').replace(' -', '')
            
            y_pos += 50
            diagnosis_lines = diagnosis.split('\n')
            line_number = 1
            for line in diagnosis_lines:
                if line.strip():  # 只处理非空行
                    # 检查是否已经有序号，如果没有则添加
                    if not line.strip()[0].isdigit():
                        line = f"{line}"
                        line_number += 1
                    
                    wrapped_lines = self.wrap_text_by_char_count(line, 40)
                    for wrapped_line in wrapped_lines:
                        draw.text((30, y_pos), wrapped_line, font=text_font, fill=(0, 0, 0))
                        y_pos += 20
            
            # 绘制治疗建议区域
            draw.text((20, y_pos+20), "治疗建议", font=header_font, fill=(25, 118, 210))
            
            # 使用AI分析结果中的治疗建议内容
            recommendation = self.extract_recommendation_from_result()
            # 删除所有无效符号
            recommendation = recommendation.replace('*', '').replace('--', '').replace('**', '').replace('#', '').replace(' -', '')
            
            y_pos += 50
            recommendation_lines = recommendation.split('\n')
            line_number = 1
            for line in recommendation_lines:
                if line.strip():  # 只处理非空行
                    # 极简测试 payload检查是否已经有序号，如果没有则添加
                    if not line.strip()[0].isdigit():
                        line = f"{line}"
                        line_number += 1
                    
                    wrapped_lines = self.wrap_text_by_char_count(line, 40)
                    for wrapped_line in wrapped_lines:
                        draw.text((30, y_pos), wrapped_line, font=text_font, fill=(0, 0, 0))
                        y_pos += 20
            
            # 添加X光图像（如果可用）- 放置在正下方
            if hasattr(self, 'xray_image') and self.xray_image:
                try:
                    # 调整图像大小以适应报告，保持原比例
                    img_ratio = self.xray_image.height / self.xray_image.width
                    new_width = 300  # 固定宽度
                    new_height = int(new_width * img_ratio)
                    xray_img = self.xray_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 放置在正下方，居中显示
                    xray_x = (img_width - new_width) // 2
                    img.paste(xray_img, (xray_x, y_pos+30))
                    draw.text((img_width//2, y_pos+new_height+40), "X光影像", font=text_font, fill=(0, 0, 0), anchor='mm')
                except Exception as e:
                    print(f"添加X光图像时出错: {e}")
            
            # 添加底部信息和免责声明极简测试 payload
            draw.rectangle([(0, y_pos+20), (img_width, y_pos+60)], fill=(240, 240, 240), outline=None)
            disclaimer = "本报告由AI辅助生成，仅供参考，最终诊断请以临床医生判断为准"
            draw.text((img_width//2, y_pos+40), disclaimer, font=small_font, fill=(100, 100, 100), anchor='mm')
            
            return img
            
        except Exception as e:
            print(f"创建美观报告时出错: {e}")
            return self.create_simple_report()

# 修改提取方法以匹配参考图片的格式
    def extract_assessment_from_result(self):
        """从分析结果中提取影像评估部分"""
        if not self.analysis_result:
            return "无影像评估内容"
        
        # 根据参考图片的格式提取内容
        if "【影像评估】" in self.analysis_result:
            start = self.analysis_result.find("【影像评估】") + 6
            end = self.analysis_result.find("【诊断结论】") if "【诊断结论】" in self.analysis_result else len(self.analysis_result)
            return self.analysis_result[start:end].strip()
        elif "影像评估" in self.analysis_result:
            start = self.analysis_result.find("影像评估") + 5
            end = self.analysis_result.find("诊断结论") if "诊断结论" in self.analysis_result else len(self.analysis_result)
            return self.analysis_result[start:end].strip()
        else:
            # 如果没有明确的分隔符，返回完整的分析结果
            return self.analysis_result
    
    def extract_diagnosis_from_result(self):
        """从分析结果极简测试 payload中提取诊断结论部分"""
        if not self.analysis_result:
            return "无诊断结论"
        
        # 根据参考图片的格式提取内容
        if "【诊断结论】" in self.analysis_result:
            start = self.analysis_result.find("【诊断结论】") + 6
            end = self.analysis_result.find("【治疗建议】") if "【治疗建议】" in self.analysis_result else len(self.analysis_result)
            return self.analysis_result[start:end].strip()
        elif "诊断结论" in self.analysis_result:
            start = self.analysis_result.find("诊断结论") + 5
            end = self.analysis_result.find("治疗建议") if "治疗建议" in self.analysis_result else len(self.analysis_result)
            return self.analysis_result[start:end].strip()
        else:
            # 如果没有明确的分隔符，返回空字符串
            return ""
    
    def extract_recommendation_from_result(self):
        """从分析结果中提取治疗建议部分"""
        if not self.analysis_result:
            return "极简测试 payload无治疗建议"
        
        # 根据参考图片的格式提取内容
        if "【治疗建议】" in self.analysis_result:
            start = self.analysis_result.find("【治疗建议】") + 6
            return self.analysis_result[start:].strip()
        elif "治疗建议" in self.analysis_result:
            start = self.analysis_result.find("治疗建议") + 5
            return self.analysis_result[start:].strip()
        else:
            # 如果没有明确的分隔符，返回空字符串
            return ""
   
    def wrap_text_precise(self, text, max_width, font):
        """更精确的文本换行算法，基于实际文本宽度"""
        lines = []
        
        # 如果没有文本，返回空列表
        if not text:
            return lines
        
        # 分割段落
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append('')
                continue
                
            words = paragraph.split(' ')
            current_line = []
            
            for word in words:
                # 测试添加这个词后的行宽度
                test_line = ' '.join(current_line + [word])
                
                # 使用临时图像测量文本宽度
                temp_img = Image.new('RGB', (1, 1))
                temp_draw = ImageDraw.Draw(temp_img)
                bbox = temp_draw.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]
                
                if text_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    
            if current_line:
                lines.append(' '.join(current_line))
                
        return lines
    
    def create_simple_report(self):
        """创建简单版本的报告（备用）"""
        img_width, img_height = 800, 1000
        img = Image.new('RGB', (img_width, img_height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("simhei.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        y_position = 10
        for line in self.get_record_text().split('\n'):
            draw.text((10, y_position), line, font=font, fill='black')
            y_position += 20
        
        return img
    
    def get_record_text(self):
        """获取完整的病历文本"""
        record = f"""患者病历报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【患者基本信息】
姓名: {self.patient_name.text()}
ID: {self.patient_id.text()}
检查日期: {self.study_date.text()}
设备极简测试 payload类型: {self.modality.text()}
检查部位: {self.body_part.text()}

【影像评估】
{self.assessment_text.toPlainText()}

【诊断结论】
{self.diagnosis_text.toPlainText()}

【治疗建议】
{self.recommendation_text.toPlainText()}

*** 本报告由AI辅助生成，仅供参考，最终诊断请以临床医生判断为准 ***
"""
        return record
    
# DeepSeek骨科专家类（使用API v3）
class DeepSeekOrthoExpert:
    def __init__(self, api_key="sk-ad5a78faa5c24c91abb2b48dc10cc5ef"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.api_url = ""
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def analyze_fracture(self, image_path, metadata=None):
        """分析X光影像"""
        if not self.api_key:
            return "错误：未设置密钥。"
        
        try:
            # 准备图像数据
            image_data = self._prepare_image_data(image_path)
            
            # 构建消息
            messages = self._build_multimodal_message(image_data)  # 传递图像数据
            
            # 调用API
            # response = self._call_deepseek_api(messages)
            
            return messages
            
        except Exception as e:
            return f"分析过程中发生错误: {str(e)}"
    

    def compress_image1(self,image_path,max_size=(512, 512), quality=85):
        """
        压缩图片以减少 Base64 编码后的长度
        
        Args:
            image_path: 图片路径
            max极简测试 payload_size: 极简测试 payload最大尺寸 (宽, 高)
            quality: JPEG 质量 (1-100)
        
        Returns:
            str: 压缩后的 Base64 编码字符串
        """
        with Image.open(image_path) as img:
            # 调整尺寸
            img.thumbnail(max_size)
            
            # 转换为 RGB (确保 JPEG 兼容性)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # 保存极简测试 payload到内存缓冲区
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            
            # 编码为 Base64
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def compress_image(self, image_path, max_width=512, quality=95):
        """
        压缩图片以减少 Base64 编码后的长度，保持原比例
        
        Args:
            image_path: 图片路径
            max_width: 最大宽度
            quality: JPEG 质量 (1-100)
        
        Returns:
            str: 压缩后的 Base64 编码字符串
        """
        with Image.open(image_path) as img:
            # 计算等比例高度
            width_percent = max_width / float(img.size[0])
            height_size = int(float(img.size[1]) * float(width_percent))
            
            # 调整尺寸，保持原比例
            img = img.resize((max_width, height_size), Image.Resampling.LANCZOS)
    
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            self.dicom_metadata=''
            # 编码为 Base64
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _prepare_image_data(self, image_path):
        """准备图像数据为base64编码"""
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                raise Exception(f"文件不存在: {image_path}")
            
            # 读取图像并转换为base64
            if image_path.lower().endswith('.dcm'):
                # DICOM文件处理
                try:
                    # 使用pydicom读取DICOM文件
                    ds = pydicom.dcmread(image_path)
                    
                    # 验证DICOM极简测试 payload文件是否包含像素数据极简测试 payload
                    if not hasattr(ds, 'pixel_array'):
                        raise Exception("DICOM文件不包含像素数据")
                    
                    # 转换DICOM数据为数组
                    img_array = self._convert_dicom_to_array(ds)
                    
                    # 确保数据在0-255范围内
                    img_array = (img_array * 255).astype(np.uint8)
                    
                    # 转换为RGB（如果是灰度图像）
                    if len(img_array.shape) == 2:
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
                    elif len(img_array.shape) == 3 and img_array.shape[2] == 4:
                        # 处理4通道图像（如RGBA）
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                    
                    # 编码为JPEG - 修复这里的错误
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 6]
                    success, encoded_image = cv2.imencode('.jpg', img_array, encode_param)
                    
                    if success:
                        # 将编码后的图像转换为base64
                        encoded_bytes = encoded_image.tobytes()
                        compressed_image_data = base64.b64encode(encoded_bytes).decode('utf-8')
                        return compressed_image_data
                    else:
                        raise Exception("JPEG编码失败")
                        
                except Exception as e:
                    # 如果DICOM处理失败，尝试作为普通图像处理
                    print(f"DICOM处理失败，尝试作为普通图像: {str(e)}")
                    compressed_image_data = self.compress_image(image_path)
                    return compressed_image_data
            else:
                # 普通图像文件
                compressed_image_data = self.compress_image(image_path)
                
                return compressed_image_data
                    
        except Exception as e:
            raise Exception(f"图像处理失败: {str(e)}")
        
        raise Exception("无法处理该图像格式")
    
    def _convert_dicom_to_array(self, dataset):
        """将DICOM像素数据转换为numpy数组"""
        try:
            # 获取像素数组
            img = dataset.pixel_array.astype(float)
            
            # 应用窗宽窗位（如果存在）
            try:
                # 处理可能的多个窗宽窗位值
                if hasattr(dataset, 'WindowCenter') and hasattr(dataset, 'WindowWidth'):
                    if isinstance(dataset.WindowCenter, pydicom.multival.MultiValue):
                        center = float(dataset.WindowCenter[0])
                    else:
                        center = float(dataset.WindowCenter)
                    
                    if isinstance(dataset.WindowWidth, pydicom.multival.MultiValue):
                        width = float(dataset.WindowWidth[0])
                    else:
                        width = float(dataset.WindowWidth)
                else:
                    # 如果没有窗宽窗位，使用图像统计信息
                    center = np.mean(img)
                    width = np.max(img) - np.min(img)
                    
                    # 极简测试 payload如果宽度为0，使用默认值
                    if width <= 0:
                        width = 1
            except:
                # 如果窗宽窗位处理失败，使用图像统计信息极简测试 payload
                center = np.mean(img)
                width = np.max(img) - np.min(img)
                if width <= 0:
                    width = 1
            
            # 应用窗宽窗位变换
            img = (img - (center - width/2)) / width
            img = np.clip(img, 0, 1)
            
            return img
            
        except Exception as e:
            raise Exception(f"DICOM转换失败: {str(e)}")
        
    def _build_multimodal_message(self, image_data):
        """构建多模态消息 - 修正版本"""
        model = ChatOpenAI(
            model_name="deepseek-chat",
            openai_api_key='sk-ad5a78faa5c24c91abb2b48dc10cc5ef',
            openai_api_base="https://api.deepseek.com/v1"
        )
    
        # 构建多模态消息，明确要求按照三个模块输出
        message = HumanMessage(
            content=json.dumps([
                {"type": "text", "text": """你是一位专业的骨科医学专家，擅长解读X光影像和骨折诊断。请为这张患者下肢骨的x光影像图提供专业、准确、简洁的医学分析，这张x光图中极有可能有骨折情况，请仔细查找。
    
    请严格按照以下三个模块格式提供分析报告：
    
    【影像评估】
    详细描述X光影像中的骨骼结构、对线情况、骨皮质连续性等，指出有无骨折征象、骨质密度等情况，重点关注胫骨和腓骨的骨折情况。
    
    【诊断结论】
    基于影像评估给出明确的诊断意见，包括有无骨折或其他骨性损伤。
    
    【治疗建议】
    根据诊断结论提供具体的治疗建议，包括是否需要进一步检查、临床随访观察等。
    
    请使用专业的医学术语，确保报告清晰、准确、简洁。"""},
                {"type": "image", "image": {"data": image_data, "format": "base64"}},
            ])
        )
    
        # 调用API
        response = model.invoke([message])
        return response.content
    
    def _call_deepseek_api(self, messages):
        """调用DeepSeek API - 增强错误处理版本"""
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
            "top_p": 0.8
        }
        
        try:
            # 发送请求并获取响应极简测试 payload
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json=payload,
                timeout=60
            )
            
            # 首先检查响应状态码[4](@极简测试 payloadref)
            if response.status_code != 200:
                error_msg = f"API返回错误状态码: {response.status_code}"
                # 尝试提取更多错误信息
                try:
                    error_data = response.json()
                    if 'error'in error_data and 'message' in error_data['error']:
                        error_msg += f", 错误信息: {error_data['error']['message']}"
                except:
                    # 如果无法解析为JSON，返回原始文本
                    error_msg += f", 响应内容: {response.text[:200]}"
                return error_msg
            
            # 检查响应内容是否为空[1,2](@ref)
            if not response.text or not response.text.strip():
                return "API返回空响应，请检查网络连接和API密钥"
            
            # 尝试解析JSON响应极简测试 payload[极简测试 payload1,2](@ref)
            try:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return "API响应格式异常，无法获取分析结果"
            except json.JSONDecodeError as e:
                return f"API返回无效JSON格式: {str(e)}，原始响应: {response.text[:200]}"
                
        except requests.exceptions.Timeout:
            return "API请求超时，请检查网络连接或稍后重试"
        except requests.exceptions.ConnectionError:
            return "网络连接错误，请检查网络连接"
        except requests.exceptions.RequestException as e:
            return f"API请求异常: {str(e)}"

class MedicalGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.zoom_factor = 1.0
        self.dragging = False
        self.last_mouse_pos = QPointF()
        self.setDragMode(QGraphicsView.NoDrag)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.background_pixmap = QPixmap("med1.png")
        self.background_item = None
        self.wave_widget = None  # 波浪等待动画控件
        self.complete_widget = None
    def show_complete_animation(self):
        """显示分析完成动画"""
        if self.complete_widget is None:
            self.complete_widget = AnalysisCompleteWidget(self.viewport())
        
        # 设置动画控件的位置和大小
        anim_size = 200
        anim_x = (self.width() - anim_size) // 2
        anim_y = (self.height() - anim_size) // 2
        
        self.complete_widget.setGeometry(anim_x, anim_y, anim_size, anim_size)
        self.complete_widget.show()
        
        # 3秒后自动隐藏
        QTimer.singleShot(3000, self.hide_complete_animation)
        
    def hide_complete_animation(self):
        """隐藏分析完成动画"""
        if self.complete_widget:
            self.complete_widget.hide()
            
    def set_background(self, visible=True):
        """动态创建背景项"""
        for item in self.scene().items():
            if isinstance(item, QGraphicsPixmapItem) and item.zValue() == -1:
                self.scene().removeItem(item)

        if visible and not self.background_pixmap.isNull():
            self.background_item = QGraphicsPixmapItem(self.background_pixmap)
            self.background_item.setZValue(-1)
            self.scene().addItem(self.background_item)
            self.fit_background()
   
    def fit_background(self):
        if self.scene() and not self.background_pixmap.isNull():
            bg_items = [item for item in self.scene().items()
                        if isinstance(item, QGraphicsPixmapItem) 
                        and item.zValue() == -1]
            if bg_items:
                self.fitInView(bg_items[0], Qt.KeepAspectRatioByExpanding)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_background()
        
    def show_wave_animation(self):
        """显示波浪等待动画"""
        if self.wave_widget is None:
            self.wave_widget = WaveWaitWidget(self.viewport())
        
        # 设置动画控件的位置和大小
        wave_width = 400
        wave_height = 150
        wave_x = (self.width() - wave_width) // 2
        wave_y = (self.height() - wave_height) // 2
        
        self.wave_widget.setGeometry(wave_x, wave_y, wave_width, wave_height)
        self.wave_widget.show()
        
    def hide_wave_animation(self):
        """隐藏波浪等待动画"""
        if self.wave_widget:
            self.wave_widget.hide()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_mouse_pos = self.mapToScene(event.pos())
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = self.mapToScene(event.pos()) - self.last_mouse_pos
            self.last_mouse_pos = self.mapToScene(event.pos())
            new_center = self.get_center() - delta
            self.centerOn(new_center)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def get_center(self):
        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        return visible_rect.center()
    
    def wheelEvent(self, event: QWheelEvent):
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
        self.measure_start_point = self.mapToScene(self.last_mouse_pos)
        self.measure_line = self.scene().addLine(QLineF())    
    
class MedicalVisionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = None
        self.current_image = None
        self.dicom_metadata = {}
        self.deepseek_expert = DeepSeekOrthoExpert()
        self.initUI()
        self.load_model()
        self.batch_images = []
        self.current_batch_index = 0
        self.file_path = ''
        self.fig_type = 0
        self.graphics_view.set_background()
        self.analyze_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        self.analyze_shortcut.activated.connect(self.deepseek_analysis)
        
    # 修改MedicalVisionApp中的generate_medical_report方法
    def generate_medical_report(self):
        """生成病历报告"""
        
        if not hasattr(self, 'last_analysis_result') or not self.last_analysis_result:
            QMessageBox.warning(self, "警告", "请先进行AI影像解读分析")
            return
        
        # 将当前图像转换为PIL图像格式
        xray_image = None
        if self.current_image is not None:
            try:
                # 将OpenCV图像转换为PIL图像
                if len(self.current_image.shape) == 3:
                    if self.current_image.shape[2] == 3:  # BGR格式
                        rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
                        xray_image = Image.fromarray(rgb_image)
                    elif self.current_image.shape[2] == 4:  # BGRA格式
                        rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGRA2RGB)
                        xray_image = Image.fromarray(rgb_image)
                else:  # 灰度图像
                    xray_image = Image.fromarray(self.current_image)
            except Exception as e:
                print(f"转换图像时出错: {e}")
        if self.fig_type == 0:
            self.dicom_metadata=''
        # 创建并显示病历对话框
        dialog = MedicalRecordDialog(
            self, 
            metadata=self.dicom_metadata,
            
            analysis_result=self.last_analysis_result
        )
        
        # 传递X光图像
        if xray_image:
            dialog.xray_image = xray_image
        
        dialog.exec_()        
    def display_image(self, img):
        self.graphics_view.set_background(False)
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        self.graphics_scene.clear()
        self.image_item = self.graphics_scene.addPixmap(pixmap)
        self.graphics_view.fitInView(self.image_item, Qt.KeepAspectRatio)
        self.graphics_view.zoom_factor = 1.0

    def clear_display(self):
        self.graphics_scene.clear()
        self.graphics_view.set_background(True)

    def initUI(self):
        self.set_medical_style()
        
        self.setWindowTitle("X-ray骨折智能检测系统v3")
        self.setMinimumSize(1400, 850)
        self.setWindowIcon(QIcon("med.png"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(15, 30, 15, 30)
        control_layout.setSpacing(20)

        self.upload_btn = QPushButton("上传单张影像")
        self.upload_btn.clicked.connect(self.open_image)
        self.upload_btn.setObjectName("actionButton")

        self.analyze_btn = QPushButton("执行骨折检测")
        self.analyze_btn.clicked.connect(self.analyze_single_image)
        self.analyze_btn.setObjectName("actionButton")

        self.deepseek_btn = QPushButton("AI助手影像解读")
        self.deepseek_btn.clicked.connect(self.deepseek_analysis)
        self.deepseek_btn.setObjectName("deepseekButton")
        self.deepseek_btn.setToolTip("使用骨科智能进行专业影像解读")

        # 新增：病历报告按钮
        self.report_btn = QPushButton("生成病历报告")
        self.report_btn.clicked.connect(self.generate_medical_report)
        self.report_btn.setObjectName("reportButton")
        self.report_btn.setToolTip("生成专业的患者病历报告")

        self.batch_btn = QPushButton("批量检测")
        self.batch_btn.clicked.connect(self.batch_process)
        self.batch_btn.setObjectName("actionButton")

        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        self.prev_btn = QPushButton("← 上一张")
        self.prev_btn.clicked.connect(self.show_prev_image)
        self.next_btn = QPushButton("下一张 →")
        self.next_btn.clicked.connect(self.show_next_image)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)

        self.batch_status = QLabel("当前: 0/0")
        self.batch_status.setAlignment(Qt.AlignCenter)
        
        self.upload_dicom_btn = QPushButton("上传DICOM影像")
        self.upload_dicom_btn.clicked.connect(self.open_dicom)
        self.upload_dicom_btn.setObjectName("actionButton")

        metadata_group = QGroupBox("DICOM元数据")
        metadata_layout = QVBoxLayout()
        self.metadata_display = QTextEdit()
        self.metadata_display.setReadOnly(True)
        self.metadata_display.setMaximumHeight(180)
        self.metadata_display.setStyleSheet("""
            QTextEdit {
                background-color: #252526;
                color: #D4D4D4;
                border: 1px solid #3A3A3A;
                font-family: Consolas;
                font-size: 9pt;
                padding: 5px;
            }
        """)
        metadata_layout.addWidget(self.metadata_display)
        metadata_group.setLayout(metadata_layout)

        deepseek_group = QGroupBox("骨科智能助手解读")
        deepseek_layout = QVBoxLayout()
        self.deepseek_display = QTextEdit()
        self.deepseek_display.setReadOnly(True)
        self.deepseek_display.setMaximumHeight(250)
        self.deepseek_display.setStyleSheet("""
            QTextEdit {
                background-color: #1E2A38;
                color: #E0F0FF;
                border: 1px solid #3A5A7A;
                font-family: 'Microsoft YaHei';
                font-size: 9.5pt;
                padding: 8px;
                line-height: 1.4;
            }
        """)
        deepseek_layout.addWidget(self.deepseek_display)
        deepseek_group.setLayout(deepseek_layout)

        control_layout.addWidget(self.upload_btn)
        control_layout.addWidget(self.upload_dicom_btn)
        control_layout.addWidget(self.analyze_btn)
        control_layout.addWidget(self.deepseek_btn)
        control_layout.addWidget(self.report_btn)  # 新增病历报告按钮
        control_layout.addWidget(self.batch_btn)
        control_layout.addWidget(nav_widget)
        control_layout.addWidget(self.batch_status)
        control_layout.addWidget(metadata_group)
        control_layout.addWidget(deepseek_group)
        control_layout.addStretch()

        self.graphics_view = MedicalGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.image_item = QGraphicsPixmapItem()
        self.graphics_scene.addItem(self.image_item)

        main_layout.addWidget(control_panel, stretch=2)
        main_layout.addWidget(self.graphics_view, stretch=5)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    # 恢复主界面原始布局和样式
    def set_medical_style(self):
        """恢复原始医疗界面样式"""
        style = """
        QMainWindow {
            background-color: #2D2D30;
        }
        QPushButton#actionButton {
            background-color: #005B96;
            color: #FFFFFF;
            border: none;
            padding: 12px 20px;
            font-size: 13px;
            border-radius: 4px;
            min-width: 120px;
            font-weight: bold;
        }
        Q极简测试 payloadPushButton#actionButton:hover {
            background-color: #007CBA;
        }
        QPushButton#deepseekButton {
            background-color: #1A6E3F;
            color: #FFFFFF;
            border: none;
            padding: 12px 20px;
            font-size: 13px;
            border-radius: 4px;
            min-width: 120px;
            font-weight: bold;
        }
        QPushButton#deepseekButton:hover {
            background-color: #218858;
        }
        QPushButton#reportButton {
            background-color: #8B4513;
            color: #FFFFFF;
            border: none;
            padding: 12px 20px;
            font-size: 13px;
            border-radius: 4px;
            min-width: 120px;
            font-weight: bold;
        }
        QPushButton#reportButton:hover {
            background-color: #A0522D;
        }
        QLabel {
            color: #D4D4D4;
            font-family: 'Segoe UI';
        }
        QGroupBox {
            color: #A0A0A0;
            font-family: 'Segoe UI';
            font-size: 10pt;
            margin-top: 12px;
            border: 1px solid #3A3A3A;
            border-radius: 4px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QTextEdit {
            background-color: #252526;
            color: #D4D4D4;
            border: 1px solid #3A3A3A;
            font-family: Consolas;
            font-size: 9pt;
            padding: 5px;
        }
        """
        self.setStyleSheet(style)
    

        
    def deepseek_analysis(self):
        if self.current_image is None:
            self.status_bar.showMessage("请先上传医学影像")
            return
    
        # 显示波浪等待动画
        self.graphics_view.show_wave_animation()
        
        # 禁用按钮防止重复操作
        self.deepseek_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        
        self.deepseek_display.setText("骨科智能助手正在分析中...\n\n请稍候，这可能需要10-30秒")
        self.status_bar.showMessage("分析中...")
        
        QApplication.processEvents()
        
        # 在实际应用中，这里应该使用线程来处理长时间操作
        # 为了简化示例，我们直接调用
        try:
            report = self.deepseek_expert.analyze_fracture(self.file_path, self.dicom_metadata)
            
            # 保存分析结果供病历报告使用
            self.last_analysis_result = report
            
            self.deepseek_display.setText(report)
            self.status_bar.showMessage("骨科智能助手解读完成", 5000)
            
            # 显示分析完成动画
            self.graphics_view.show_complete_animation()
            
        except Exception as e:
            self.deepseek_display.setText(f"分析过程中发生错误: {str(e)}")
            self.status_bar.showMessage("分析失败", 5000)
            
        finally:
            # 隐藏波浪等待动画
            self.graphics_view.hide_wave_animation()
            # 重新启用按钮
            self.deepseek_btn.setEnabled(True)
            self.analyze_btn.setEnabled(True)
        
    def open_dicom(self):
        options = QFileDialog.Options()
        self.file_path, _ = QFileDialog.getOpenFileName(
            self, "选择DICOM文件", "", 
            "DICOM文件 (*.dcm)", options=options
        )
        
        if self.file_path:
            try:
                ds = pydicom.dcmread(self.file_path)
                self.dicom_metadata = self.extract_dicom_metadata(ds)
                
                img_array = self.convert_dicom_to_array(ds)
                self.current_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                self.show_metadata()
                self.display_image(self.current_image)
                self.fig_type = 1
                
                self.deepseek_display.setText("点击\"AI助手影像解读\"按钮获取专业分析")
                
            except Exception as e:
                self.status_bar.showMessage(f"DICOM文件读取失败: {str(e)}")

    def extract_dicom_metadata(self, dataset):
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
        img = dataset.pixel_array.astype(float)
        
        center = int(dataset.WindowCenter) if 'WindowCenter' in dataset else img.mean()
        width = int(dataset.WindowWidth) if 'WindowWidth' in dataset else img.max() - img.min()
        
        img = (img - (center - width/2)) / width
        img = np.clip(img, 0, 1)
        img = (img * 255).astype(np.uint8)
        
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        return img

    def show_metadata(self):
        metadata_str = "=== 患者信息 ===\n"
        for key, value in self.dicom_metadata.items():
            metadata_str += f"{key}: {value}\n"
        self.metadata_display.setText(metadata_str)
        
    def reset_view(self):
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
        if event.key() == Qt.Key_Left:
            self.show_prev_image()
        elif event.key() == Qt.Key_Right:
            self.show_next_image()

    def update_navigation(self):
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
        if self.batch_images:
            img = self.batch_images[self.current_batch_index]
            self.display_image(img)
            self.update_navigation()

    def batch_process(self):
        folder = QFileDialog.getExistingDirectory(self, "选择医学影像文件夹")
        if not folder:
            return

        valid_ext = ['.jpg', '.jpeg', '.png']
        image_files = [
            os.path.join(folder, f) for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in valid_ext
        ]

        if not image_files:
            self.status_bar.showMessage("文件夹中没有支持的图像文件")
            return

        self.metadata_display.setText('None')
        self.deepseek_display.setText("批量处理模式极简测试 payload中，请选择单张影像进行智能解读")
        progress = QProgressDialog("批量处理中...", "取消", 0, len(image_files), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        self.batch_images.clear()
        self.current_batch_index = 0

        for i, file_path in enumerate(image_files):
            if progress.wasCanceled():
                break

            try:
                analyzed_img = jiance.run(figtype=0, source=file_path)
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
        self.fig_type = 0
        self.metadata_display.setText('None')
        self.deepseek_display.setText("点击\"AI助手影像解读\"按钮获取专业分析")
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
        if self.current_image is None:
            self.status_bar.showMessage("请先上传医学影像")
            return

        self.batch_images.clear()
        self.current_batch_index = 0
        self.analyzed_image = jiance.run(figtype=self.fig_type, source=self.file_path)
        self.display_image(self.analyzed_image)
        self.reset_view()
        self.deepseek_display.setText("检测完成，点击\"AI助手影像解读\"按钮获取详细分析")

    def resizeEvent(self, event):
        if self.current_image is not None:
            self.display_image(self.current_image)
            self.reset_view()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MedicalVisionApp()
    window.show()
    sys.exit(app.exec_())