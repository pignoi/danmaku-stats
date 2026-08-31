from .data_filter import GenStats

class DanmakuStats(GenStats):
    def __init__(self, platform: str, room_id):
        
        avail_info = "danmaku"
        info_sheet_name = "danmaku"

        super().__init__(platform, room_id, avail_info = avail_info, info_sheet_name=info_sheet_name)

    def update_function(self, normalize_bool: bool=False, send_count:int=100, ignore_words:list=["?","？","1"], plot_top:int=10):

        """
        对弹幕的文本信息进行提取的函数。
        normalize_bool: 是否对数据进行百分比处理
        ignore_words: 统计结果中不希望出现的词汇/关键词
        plot_top: 统计结果中希望表现出的个数
        """
        
        if self.static_data.empty:
            raise ValueError("Data is Empty.")
        else:
            data = self.static_data

        danmaku_data = data["context"]
        danmaku_data = danmaku_data[~danmaku_data.isin(ignore_words)]
        
        danmaku_counts = danmaku_data.value_counts(normalize=normalize_bool)
        # danmaku_percents = danmaku_counts.values / np.sum(danmaku_counts.values)
        
        counts_pdf = danmaku_counts.reset_index()
        counts_pdf.columns = ['context', 'count']

        danmaku_sorted = counts_pdf["context"]
        counts_sorted = counts_pdf["count"]

        to_send_danmakus = danmaku_sorted.to_list()[:send_count]
        to_send_counts = counts_sorted.to_list()[:send_count]

        return {"fig": None, "origin_data": {"showinfos": to_send_danmakus, "counts": to_send_counts}}
    
