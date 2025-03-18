import sys
import os
import requests
from io import BytesIO
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QFont
from pytubefix import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip

class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(300, 200, 450, 450)
        self.setStyleSheet("background-color: #c0c7d1;")

        self.label = QLabel("Enter YouTube URL", self)
        self.label.setFont(QFont("Arial", 14, QFont.Bold))

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Paste YouTube URL here...")
        self.url_input.setStyleSheet("padding: 5px; font-size: 12px;")

        self.search_button = QPushButton("Search", self)
        self.search_button.setStyleSheet("background-color: #34495E; color: white; font-size: 12px; padding: 5px;")
        self.search_button.clicked.connect(self.search_video)

        self.thumbnail_label = QLabel(self)
        self.thumbnail_label.setStyleSheet("border: 1px solid black; background: white; text-align: center;")
        self.thumbnail_label.setFixedSize(320, 180)

        self.video_title = QLabel("", self)
        self.video_title.setFont(QFont("Arial", 12, QFont.Bold))

        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("font-size: 12px; color: blue;")

        self.download_button = QPushButton("Download", self)
        self.download_button.setStyleSheet("background-color: #2980B9; color: white; font-size: 12px; padding: 5px;")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.download_video)

        self.retry_button = QPushButton("Retry", self)
        self.retry_button.setStyleSheet("background-color: #E74C3C; color: white; font-size: 12px; padding: 5px;")
        self.retry_button.setEnabled(False)
        self.retry_button.clicked.connect(self.reset_ui)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.search_button)
        layout.addWidget(self.video_title)
        layout.addWidget(self.thumbnail_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.download_button)
        layout.addWidget(self.retry_button)
        self.setLayout(layout)

    def search_video(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a valid YouTube URL.")
            return
        
        try:
            yt = YouTube(url)
            self.video_title.setText(yt.title)
            self.status_label.setText("Video found. Please confirm and download.")
            self.display_thumbnail(yt.thumbnail_url)
            
            self.download_button.setEnabled(True)
            self.retry_button.setEnabled(True)
            self.current_video = yt
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch video details.\n{str(e)}")
            self.status_label.setText("Invalid video. Please check the URL.")

    def display_thumbnail(self, url):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            image_data = response.content

            pixmap = QPixmap()
            pixmap.loadFromData(image_data)

            if pixmap.isNull():
                raise ValueError("Failed to load thumbnail image.")

            self.thumbnail_label.setPixmap(pixmap)
            self.thumbnail_label.setScaledContents(True)
        except Exception as e:
            self.status_label.setText("Failed to load thumbnail.")

    def download_video(self):
        if not hasattr(self, "current_video"):
            QMessageBox.warning(self, "Error", "No video selected. Please search first.")
            return

        yt = self.current_video

        try:
            download_path = QFileDialog.getExistingDirectory(self, "Select Download Folder")
            if not download_path:
                return

            safe_title = yt.title.replace(" ", "_").replace("/", "_").replace("\\", "_")
            video_file = os.path.join(download_path, f"{safe_title}_video.mp4")
            audio_file = os.path.join(download_path, f"{safe_title}_audio.mp4")
            output_file = os.path.join(download_path, f"{safe_title}_HQ.mp4")

            video_stream = yt.streams.filter(adaptive=True, file_extension="mp4").order_by("resolution").desc().first()
            audio_stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()

            if not video_stream or not audio_stream:
                QMessageBox.critical(self, "Error", "No available streams for this video.")
                return

            self.status_label.setText("Downloading video...")
            video_stream.download(output_path=download_path, filename=f"{safe_title}_video.mp4")

            self.status_label.setText("Downloading audio...")
            audio_stream.download(output_path=download_path, filename=f"{safe_title}_audio.mp4")

            self.status_label.setText("Merging video and audio...")
            self.merge_video_audio(video_file, audio_file, output_file)

            self.status_label.setText("Download Complete!")
            QMessageBox.information(self, "Download Complete", f"Video saved at:\n{output_file}")

        except Exception as e:
            QMessageBox.critical(self, "Download Error", str(e))

    def merge_video_audio(self, video_file, audio_file, output_file):
        try:
            video_clip = VideoFileClip(video_file)
            audio_clip = AudioFileClip(audio_file)
            final_clip = video_clip.set_audio(audio_clip)
            final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")

            video_clip.close()
            audio_clip.close()
            final_clip.close()

            os.remove(video_file)
            os.remove(audio_file)

        except Exception as e:
            QMessageBox.critical(self, "FFmpeg Error", f"Failed to process video.\n{str(e)}")

    def reset_ui(self):
        self.url_input.clear()
        self.video_title.clear()
        self.thumbnail_label.clear()
        self.status_label.clear()
        self.download_button.setEnabled(False)
        self.retry_button.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())
