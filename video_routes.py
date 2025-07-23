import ffmpeg
from flask import Blueprint, request, jsonify, send_file

video_bp = Blueprint('video', __name__)

@video_bp.route('/video', methods=['POST'])
def generate_video():
    data = request.get_json(force=True) or {}
    ingredients = data.get("ingredients", [])
    if not ingredients:
        return jsonify(error="Missing ingredients list"), 400

    # Always generate placeholder with visible overlay
    (
        ffmpeg
        .input('color=c=black:s=640x480:d=5', f='lavfi', r=25)
        .filter('drawtext',
                text=f"Ingredients: {','.join(ingredients)}",
                fontfile="C\:/Windows/Fonts/arial.ttf",
                fontcolor='white',
                fontsize=32,
                x='(w-text_w)/2',
                y='(h-text_h)/2')
        .output('output.mp4', vcodec='libx264', pix_fmt='yuv420p')
        .overwrite_output()
        .run()
    )
    return send_file('output.mp4', mimetype='video/mp4')
