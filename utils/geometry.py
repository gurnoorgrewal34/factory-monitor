def calculate_iou(boxA, boxB):
    """
    Calculates IoU between two boxes.

    box = [x1, y1, x2, y2]
    """

    ax1, ay1, ax2, ay2 = map(float, boxA)
    bx1, by1, bx2, by2 = map(float, boxB)

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_width = max(0, inter_x2 - inter_x1)
    inter_height = max(0, inter_y2 - inter_y1)

    intersection = inter_width * inter_height

    areaA = (ax2 - ax1) * (ay2 - ay1)
    areaB = (bx2 - bx1) * (by2 - by1)

    union = areaA + areaB - intersection

    if union <= 0:
        return 0.0

    return intersection / union