import unittest
from unittest.mock import patch, MagicMock, call
import cv2
from src.core.camera import Camera

class TestCameraPipeline(unittest.TestCase):
    @patch('src.core.camera.cv2.VideoCapture')
    @patch('src.core.camera.Camera._check_gstreamer_plugin')
    def test_start_primary_pipeline_success(self, mock_check_plugin, mock_video_capture):
        # Setup
        cam = Camera(width=1536, height=864, fps=30)
        mock_check_plugin.return_value = True

        # Mock success on first try
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, MagicMock(size=100))
        mock_video_capture.return_value = mock_cap

        # Action
        cam.start()

        # Assert
        expected_pipeline = (
            "libcamerasrc ! video/x-raw, width=1536, height=864, framerate=30/1 ! "
            "videoconvert ! video/x-raw, format=BGR ! appsink drop=1 sync=0"
        )
        mock_video_capture.assert_called_with(expected_pipeline, cv2.CAP_GSTREAMER)

    @patch('src.core.camera.cv2.VideoCapture')
    @patch('src.core.camera.Camera._check_gstreamer_plugin')
    def test_start_fallback_pipeline_success(self, mock_check_plugin, mock_video_capture):
        # Setup
        cam = Camera(width=1536, height=864, fps=30)
        mock_check_plugin.return_value = True

        # Mock failure on first try, success on second
        mock_cap_fail = MagicMock()
        mock_cap_fail.isOpened.return_value = False

        mock_cap_success = MagicMock()
        mock_cap_success.isOpened.return_value = True
        mock_cap_success.read.return_value = (True, MagicMock(size=100))

        # side_effect for multiple calls
        mock_video_capture.side_effect = [mock_cap_fail, mock_cap_success]

        # Action
        cam.start()

        # Assert
        expected_pipeline_primary = (
            "libcamerasrc ! video/x-raw, width=1536, height=864, framerate=30/1 ! "
            "videoconvert ! video/x-raw, format=BGR ! appsink drop=1 sync=0"
        )
        expected_pipeline_fallback = (
            "libcamerasrc ! videoconvert ! video/x-raw, format=BGR ! appsink drop=1 sync=0"
        )

        calls = [
            call(expected_pipeline_primary, cv2.CAP_GSTREAMER),
            call(expected_pipeline_fallback, cv2.CAP_GSTREAMER)
        ]
        mock_video_capture.assert_has_calls(calls)

if __name__ == '__main__':
    unittest.main()
