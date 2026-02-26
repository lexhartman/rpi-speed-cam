import unittest
import subprocess
from unittest.mock import patch, MagicMock
from src.core.camera import Camera

class TestCameraVerification(unittest.TestCase):
    @patch('src.core.camera.subprocess.run')
    def test_check_gstreamer_plugin_found(self, mock_run):
        # Setup
        cam = Camera()
        mock_run.return_value.returncode = 0

        # Action
        result = cam._check_gstreamer_plugin("libcamerasrc")

        # Assert
        self.assertTrue(result)
        mock_run.assert_called_with(["gst-inspect-1.0", "libcamerasrc"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @patch('src.core.camera.subprocess.run')
    def test_check_gstreamer_plugin_not_found_error(self, mock_run):
        # Setup
        cam = Camera()
        mock_run.side_effect = subprocess.CalledProcessError(1, ["gst-inspect-1.0"])

        # Action
        result = cam._check_gstreamer_plugin("libcamerasrc")

        # Assert
        self.assertFalse(result)

    @patch('src.core.camera.subprocess.run')
    def test_check_gstreamer_plugin_not_found_file(self, mock_run):
        # Setup
        cam = Camera()
        mock_run.side_effect = FileNotFoundError()

        # Action
        result = cam._check_gstreamer_plugin("libcamerasrc")

        # Assert
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
