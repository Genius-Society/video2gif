import os
import math
import gradio as gr
from PIL import Image, ImageSequence
from moviepy.editor import VideoFileClip
from utils import clean_dir, TMP_DIR, EN_US

ZH2EN = {
    "倍速": "Speed",
    "状态栏": "Status",
    "文件名": "Filename",
    "下载动图": "Download GIF",
    "视频过长": "Video too long",
    "视频转 GIF 动图": "Video to GIF",
    "上传视频 (请确保完整上传再点击提交，若时长超过五秒可先在线裁剪)": "Upload video (please ensure the video is completely uploaded before clicking submit, you can crop it online to < 5s)",
}


def _L(zh_txt: str):
    return ZH2EN[zh_txt] if EN_US else zh_txt


def get_frame_dur(gif: Image):
    # 获取 GIF 图像中第一帧的 duration
    dur = gif.info.get("duration", 100)
    # 返回每一帧的 duration
    return [frame.info.get("duration", dur) for frame in ImageSequence.Iterator(gif)]


def resize_gif(target_width: int, target_height: int, input_gif, output_gif):
    gif = Image.open(input_gif)
    modified_frames = []
    for frame in ImageSequence.Iterator(gif):
        resized_frame = frame.resize((target_width, target_height), Image.LANCZOS)
        modified_frames.append(resized_frame)

    frame_durations = get_frame_dur(gif)
    # 将修改后的帧作为新的 GIF 保存
    modified_frames[0].save(
        output_gif,
        format="GIF",
        append_images=modified_frames[1:],
        save_all=True,
        duration=frame_durations,
        loop=0,
    )

    return output_gif


# outer func
def infer(video_path: str, speed: float, target_w=640, cache=f"{TMP_DIR}/gif"):
    status = "Success"
    gif_name = gif_out = None
    try:
        clean_dir(cache)
        with VideoFileClip(video_path, audio_fps=16000) as clip:
            if clip.duration > 5:
                raise ValueError(_L("视频过长"))

            clip.speedx(speed).to_gif(f"{cache}/input.gif", fps=12)
            w, h = clip.size

        gif_in = f"{cache}/input.gif"
        target_h = math.ceil(target_w * h / w)
        gif_name = os.path.basename(video_path)
        gif_out = resize_gif(target_w, target_h, gif_in, f"{cache}/output.gif")

    except Exception as e:
        status = f"{e}"

    return status, gif_name, gif_out


if __name__ == "__main__":
    example = (
        "https://www.modelscope.cn/studio/Genius-Society/video2gif/resolve/master"
        if EN_US
        else "."
    )
    gr.Interface(
        fn=infer,
        inputs=[
            gr.Video(
                label=_L(
                    "上传视频 (请确保完整上传再点击提交，若时长超过五秒可先在线裁剪)"
                )
            ),
            gr.Slider(label=_L("倍速"), minimum=0.5, maximum=2.0, step=0.25, value=1.0),
        ],
        outputs=[
            gr.Textbox(label=_L("状态栏"), buttons=["copy"]),
            gr.Textbox(label=_L("文件名"), buttons=["copy"]),
            gr.Image(
                label=_L("下载动图"),
                type="filepath",
                buttons=["download", "fullscreen"],
            ),
        ],
        flagging_mode="never",
        examples=[[f"{example}/examples/herta.mp4", 2]],
        cache_examples=False,
        title=_L("视频转 GIF 动图"),
    ).launch(css="#gradio-share-link-button-0 { display: none; }")
