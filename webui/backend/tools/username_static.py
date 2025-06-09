from .data_filter import GenStats

class UsernameStats(GenStats):
    def __init__(self, platform: str, room_id):
        
        avail_info = "username"
        info_sheet_name = "danmaku"

        super().__init__(platform, room_id, avail_info = avail_info, info_sheet_name=info_sheet_name)

    def update_function(self, normalize: bool=False, send_count:int=100, plot_top:int=10):
        
        """
        对发送弹幕的用户id信息进行提取的函数。
        normalize: 是否对数据进行百分比处理
        plot_top: 统计结果中希望表现出的个数
        """
        if self.static_data.empty:
            raise ValueError("Data is Empty.")
        else:
            data = self.static_data

        username_data = data["username"]
        
        username_counts = username_data.value_counts(normalize=normalize)
        # danmaku_percents = danmaku_counts.values / np.sum(danmaku_counts.values)
        
        counts_pdf = username_counts.reset_index()
        counts_pdf.columns = ['context', 'count']

        username_sorted = counts_pdf["context"]
        counts_sorted = counts_pdf["count"]

        to_send_usernames = username_sorted.to_list()[:send_count]
        to_send_counts = counts_sorted.to_list()[:send_count]

        # 对用户名进行部分打码处理
        username_mask = True
        
        if username_mask == True:
            for list_index, username in enumerate(to_send_usernames):
                username_length = len(username)
                username_str_list = [i for i in username]
                
                # 将第一个字符和最后一个字符打码
                username_str_list[0] = "*"
                username_str_list[-1] = "*"

                # 如果用户名称总数大于5，则将其中间的一个字符也打码
                if username_length > 5:
                    mid_index = int(username_length/2)
                    username_str_list[mid_index] = "*"
                
                final_username = "".join(username_str_list)
                to_send_usernames[list_index] = final_username

        # 前n名弹幕画图
        # danmaku_topn = danmaku_sorted[0: plot_top]
        # count_topn = danmaku_counts[0: plot_top]
        # plot_top = count_topn.shape[0]
        # for num, i in enumerate(danmaku_topn):    # 处理b站表情包的长链接
        #     if "http://i0.hdslb.com" in i:
        #         mes_list = i.split('(')[:-1]
        #         danmaku_topn[num] = f"{'('.join(mes_list)}(表情包)"
        
        # normal_style()
        # plot_labels = ['\n'.join(wrap(i, width=12)) for i in danmaku_topn[::-1]]
        # plot_values = count_topn[::-1]
        
        fig = None
        # fig, ax = plt.subplots()
        # for y, x in enumerate(plot_values):
        #     ax.text(x - 0.1, y, str(x), va='center', ha="right", fontsize=10)  # 数值标签位置
        # ax.barh(plot_labels, plot_values, color='skyblue')
        
        # ax.set_yticks(range(plot_top))  # 确保刻度位置与标签对应
        # ax.set_yticklabels(plot_labels, rotation=30, fontsize=int(80/plot_top))  # 旋转一定角度，水平对齐为右

        return {"fig":fig, "origin_data":{"showinfos":to_send_usernames, "counts":to_send_counts}}
