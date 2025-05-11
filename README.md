# LungMaskEditor 🫁🖌️

An interactive GUI tool for editing lung region segmentation masks based on chest X-ray images. Designed for research and annotation refinement tasks in medical imaging workflows.

## Features

- Load paired lung images and binary mask files
- Visualize lung images overlaid with mask contours
- Add/remove mask regions using mouse brush
- Adjustable brush size and drawing mode (add/remove)
- Undo editing history
- Keyboard shortcuts for rapid editing
- Save edited masks back to original folder

## Keyboard Shortcuts

| Key | Function              |
|-----|-----------------------|
| A   | Add region (white)    |
| R   | Remove region (black) |
| S   | Save current mask     |
| Ctrl+Z | Undo last action   |
| ←/→  | Navigate images      |
| +/- | Adjust brush size     |

## Installation

```bash
pip install opencv-python pillow tkinter numpy
```

## Run the App

```bash
python lung_mask_editor.py
```

## License

This tool is licensed for **personal, non-commercial use only**.  
Commercial use is strictly prohibited without written permission.

📧 Contact: yu-zhiqian@outlook.com  
© 2025 Zhiqian Yu
