from typing import Any, Dict, List, Optional

from app.core.middleware import get_current_active_user
from app.models.user import User
from app.services.minimax_client import MinimaxAPIError
from app.services.voice_service import voice_service
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


class VoiceSynthesisRequest(BaseModel):
    text: str = Field(..., description="待合成的文本")
    model: str = Field("speech-2.6-hd", description="语音模型")
    voice_id: Optional[str] = Field(
        None, description="音色ID，传空由服务端选择默认音色"
    )
    speed: float = Field(1.0, ge=0.5, le=2.0, description="语速，0.5~2.0")
    vol: Optional[float] = Field(1.0, gt=0, le=10, description="音量")
    pitch: Optional[float] = Field(0.0, ge=-12, le=12, description="语调")
    emotion: Optional[str] = Field(
        None, description="情绪标签，可选 happy/sad/angry/... 等"
    )
    sample_rate: Optional[int] = Field(None, description="采样率")
    bitrate: Optional[int] = Field(None, description="比特率")
    format: Optional[str] = Field("mp3", description="音频格式")
    channel: Optional[int] = Field(1, ge=1, le=2, description="声道")
    output_format: str = Field("url", description="返回格式 url/hex")
    stream: bool = Field(False, description="是否流式输出")
    subtitle_enable: bool = Field(False, description="是否生成字幕")
    aigc_watermark: bool = Field(False, description="是否添加水印")
    language_boost: Optional[str] = Field(None, description="小语种/方言增强")
    text_normalization: Optional[bool] = Field(None, description="是否开启文本规范化")
    latex_read: Optional[bool] = Field(None, description="是否朗读 LaTeX 公式")
    pronunciation_dict: Optional[Dict[str, Any]] = Field(
        None, description="自定义发音词典"
    )
    stream_options: Optional[Dict[str, Any]] = Field(None, description="流式配置")
    timber_weights: Optional[List[Dict[str, Any]]] = Field(
        None, description="混合音色设置"
    )
    provider: Optional[str] = Field(
        None, description="指定语音提供商，默认使用首个可用提供商"
    )


class VoiceDesignRequest(BaseModel):
    prompt: str = Field(..., description="音色描述")
    preview_text: str = Field(..., description="试听文本")
    voice_id: Optional[str] = Field(None, description="可选的自定义 voice_id")
    aigc_watermark: bool = Field(False, description="试听音频是否加水印")
    provider: Optional[str] = Field(None, description="语音提供商")


class VoiceDeleteRequest(BaseModel):
    voice_type: str = Field(..., description="voice_cloning / voice_generation")
    voice_id: str = Field(..., description="待删除的 voice_id")
    provider: Optional[str] = Field(None, description="语音提供商")


class MusicGenerationRequest(BaseModel):
    model: str = Field("music-2.0", description="音乐模型")
    prompt: str = Field(..., description="音乐描述")
    lyrics: str = Field(..., description="歌词")
    stream: bool = Field(False, description="是否流式返回")
    output_format: str = Field("hex", description="输出格式 url/hex，流式下仅支持 hex")
    sample_rate: Optional[int] = Field(None, description="采样率")
    bitrate: Optional[int] = Field(None, description="比特率")
    format: Optional[str] = Field("mp3", description="音频格式")
    aigc_watermark: bool = Field(False, description="是否添加水印")
    provider: Optional[str] = Field(None, description="语音提供商")


@router.get("/enums")
async def list_voice_enums(current_user: User = Depends(get_current_active_user)):
    """返回可选枚举（中英文对照）"""
    enums = voice_service.enums()
    return {"success": True, "data": enums}


@router.get("/voices")
async def list_voices(
    voice_type: str = Query(
        "all", description="音色类型 system/voice_cloning/voice_generation/all"
    ),
    provider: Optional[str] = Query(None, description="指定提供商"),
    refresh: bool = Query(False, description="是否强制刷新远端列表"),
    current_user: User = Depends(get_current_active_user),
):
    try:
        result = await voice_service.list_voices(
            voice_type=voice_type, provider=provider, force_refresh=refresh
        )
        return {"success": True, "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except MinimaxAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"音色查询失败: {exc}")


@router.post("/tts")
async def synthesize_voice(
    request: VoiceSynthesisRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        output_format = request.output_format
        if request.stream and output_format == "url":
            output_format = "hex"

        result = await voice_service.synthesize(
            provider=request.provider,
            text=request.text,
            model=request.model,
            voice_id=request.voice_id,
            speed=request.speed,
            vol=request.vol,
            pitch=request.pitch,
            emotion=request.emotion,
            sample_rate=request.sample_rate,
            bitrate=request.bitrate,
            format=request.format,
            channel=request.channel,
            output_format=output_format,
            stream=request.stream,
            subtitle_enable=request.subtitle_enable,
            aigc_watermark=request.aigc_watermark,
            language_boost=request.language_boost,
            text_normalization=request.text_normalization,
            latex_read=request.latex_read,
            pronunciation_dict=request.pronunciation_dict,
            stream_options=request.stream_options,
            timber_weights=request.timber_weights,
        )
        return {"success": True, "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except MinimaxAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"语音合成失败: {exc}")


@router.post("/design")
async def design_voice(
    request: VoiceDesignRequest, current_user: User = Depends(get_current_active_user)
):
    try:
        result = await voice_service.design_voice(
            prompt=request.prompt,
            preview_text=request.preview_text,
            voice_id=request.voice_id,
            aigc_watermark=request.aigc_watermark,
            provider=request.provider,
        )
        return {"success": True, "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except MinimaxAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"音色设计失败: {exc}")


@router.delete("/voices/{voice_id}")
async def delete_voice(
    voice_id: str,
    request: VoiceDeleteRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        result = await voice_service.delete_voice(
            voice_type=request.voice_type, voice_id=voice_id, provider=request.provider
        )
        return {"success": True, "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except MinimaxAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"删除音色失败: {exc}")


@router.post("/music")
async def generate_music(
    request: MusicGenerationRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        output_format = request.output_format
        if request.stream:
            output_format = "hex"
        result = await voice_service.generate_music(
            provider=request.provider,
            model=request.model,
            prompt=request.prompt,
            lyrics=request.lyrics,
            stream=request.stream,
            output_format=output_format,
            sample_rate=request.sample_rate,
            bitrate=request.bitrate,
            format=request.format,
            aigc_watermark=request.aigc_watermark,
        )
        return {"success": True, "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except MinimaxAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"音乐生成失败: {exc}")
