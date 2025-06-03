from .data_filter import GenStats

class DesuwaStats(GenStats):
    def __init__(self, platform: str, room_id):

        avail_info = "desuwa"
        update_times = {"1days":"", "100000days":""}

        super().__init__(platform, room_id, avail_info, update_times)
