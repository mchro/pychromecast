"""Controller to interface with the DRTV app, from the Danish Broadcasting Corporation, dr.dk"""
import threading
import json

from .media import STREAM_TYPE_BUFFERED, STREAM_TYPE_LIVE, MESSAGE_TYPE, TYPE_LOAD, BaseMediaPlayer
from .. import __version__
from ..config import APP_DRTV
from ..error import PyChromecastError

APP_NAMESPACE = "urn:x-cast:com.google.cast.media"


class DRTVController(BaseMediaPlayer):
    """Controller to interact with DRTV app."""

    def __init__(self):
        super().__init__(APP_DRTV)

    def play_drtv(  # pylint: disable=too-many-locals
        self,
        media_id,
        dr_session_tokens,
        is_live=False,
        current_time=0,
        autoplay=True,
        chainplay_countdown=10,
        callback_function=None,
    ):
        """
        Play DRTV media.

        Parameters:
        media_id: the id of the media to play, e.g. 20875
        dr_session_tokens: JWT tokens to allow access to the content
        chainplay_countdown: seconds to countdown before the next media in the chain (typically next episode) is played. -1 to disable
        """
        stream_type = STREAM_TYPE_LIVE if is_live else STREAM_TYPE_BUFFERED

        session_tokens = json.loads(dr_session_tokens)
        account_token = next((t for t in session_tokens if t['type'] == 'UserAccount'), {})
        profile_token = next((t for t in session_tokens if t['type'] == 'UserProfile'), {})

        msg = {
            "media": {
                "contentId": media_id,
                "contentType": "video/hls",
                "streamType": stream_type,
                "metadata": {},
                "customData": {
                    "accessService": "StandardVideo"
                },
            },
            MESSAGE_TYPE: TYPE_LOAD,
            "currentTime": current_time,
            "autoplay": autoplay,
            "customData": {
                "accountToken": account_token,
                "chainPlayCountdown": chainplay_countdown,
                "profileToken": profile_token,
                "senderAppVersion": __version__,
                "senderDeviceType": "pyChromeCast",
                "showDebugOverlay": False,
                "userId": ""
            },
        }
        self.send_message(msg, inc_session_id=True, callback_function=callback_function)

    # pylint: disable-next=arguments-differ
    def quick_play(self, media_id, dr_tokens, **kwargs):
        """
        Quick Play

        Parameters:
        media_id: the id of the media to play, e.g. 20875
        dr_session_tokens: JWT tokens to allow access to the content
        """
        play_media_done_event = threading.Event()

        def play_media_done(_):
            play_media_done_event.set()

        self.play_drtv(
            media_id,
            dr_tokens,
            callback_function=play_media_done,
            **kwargs
        )

        play_media_done_event.wait(30)
        if not play_media_done_event.is_set():
            raise PyChromecastError()