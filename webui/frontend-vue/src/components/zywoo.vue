<template>
  <div class="container">
    <!-- 右上角导航栏 -->
    <div class="navbar">
      <a href="https://github.com/pignoi/danmaku-stats" target="_blank" class="nav-link">
        <img src="https://media.axuan.wang/github.png" class="sponsor-img" />
      </a>
      <a href="#" class="nav-link" @click="showSponsorModal = true">
        <img src="https://media.axuan.wang/sponsor.png" alt="赞助" class="sponsor-img" />
      </a>
    </div>

    <!-- 赞助弹框 -->
    <div v-if="showSponsorModal" class="modal-overlay" @click="showSponsorModal = false">
      <div class="modal-content" @click.stop>
        <img src="https://media.axuan.wang/skm.png" alt="赞助方式" class="sponsor-image" />
        <button class="close-button" @click="showSponsorModal = false">关闭</button>
      </div>
    </div>

    <!-- 上部 15%：时间尺度、时间单位和确定按钮 -->
    <div class="top-section">
      <div class="form">
        <div class="form-row">
          <div class="form-group">
            <label> {{infoLabel}} </label>
          </div>
        </div>

        <div class="form-row">

          
          <div class="form-group">
            <label for="timeLength">类型:</label>
            <select class="top-select" id="timeLength" v-model="selectedInfoName">
              <option v-for="option in infoNameOptions" :key="option" :value="option">
                {{ option }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="timeLength">时长:</label>
            <select class="top-select" id="timeLength" v-model="selectedTimeLength">
              <option v-for="option in timeOptions" :key="option" :value="option">
                {{ option }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <button @click="fetchData">确定</button>
          </div>
        </div>

      </div>
    </div>
    <!-- 中部的10…% -->
    <div class="mid-section">
      <div class="mid-background">
        <a href="https://wjq6657.top/">回到弹幕统计界面</a>
      </div>
      <div class="mid-background">
        <a href="https://wjq6657.top/desuwa">前往desuwa统计界面</a>
      </div>
    </div>
    <!-- 下部 85%：结果表格 -->
    <div class="bottom-section">
      <div v-if="tableData.length > 0" class="table-container">
        <table>
          <thead>
            <tr>
              <th>{{selectedInfoName}}</th>
              <th>次数</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in paginatedData" :key="index">
              <td>{{ item.name }}</td>
              <td>{{ item.value }}</td>
              <td>
                <button @click="copyToClipboard(item.name)">复制</button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 分页控件 -->
        <div class="pagination">
          <button @click="prevPage" :disabled="currentPage === 1">上一页</button>
          <span>第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
          <button @click="nextPage" :disabled="currentPage === totalPages">下一页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      infoLabel: "",    // 初始的信息显示框
      platform: this.$route.query.platform, // 从路由参数中获取平台
      room_id: this.$route.query.room_id, // 从路由参数中获取房间号码
      selectedInfoName: "弹幕",
      selectedTimeLength: "历史统计", // 默认时间长度
      infoNameOptions: ["弹幕", "圣人id"],
      timeOptions: ["1分钟", "1小时", "1天", "历史统计"], // 默认时间选项（分钟）
      tableData: [], // 全部表格数据
      currentPage: 1, // 当前页码
      itemsPerPage: 10, // 每页显示的数据条数
      showSponsorModal: false,
      infoNameDict:{
        "弹幕": "danmaku",
        "圣人id": "username"
      }
    };
  },
  computed: {
    // 计算分页后的数据
    paginatedData() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.tableData.slice(start, end);
    },
    // 计算总页数
    totalPages() {
      return Math.ceil(this.tableData.length / this.itemsPerPage);
    },
  },
  watch: {
    // 监听时间尺度变化
    selectedTimeLength() {
      this.fetchData(); // 自动更新数据
    },
    selectedInfoName() {
      this.fetchData(); // 自动更新数据
    },
  },
  methods: {
    // 获取数据
    async fetchData() {
      let post_timeunit = null;
      let post_timevalue = null;

      let temp_infoLabel = null;

      let names = null;
      let values = null;
      let last_update = null;
      
      if (this.selectedTimeLength === "1分钟") {
        post_timeunit = "minutes";
        post_timevalue = "1";
        temp_infoLabel = "玩机器直播间1分钟内zywoo弹幕统计";
      };
      if (this.selectedTimeLength === "1小时") {
        post_timeunit = "hours";
        post_timevalue = "1";
        temp_infoLabel = "玩机器直播间1小时内zywoo弹幕统计";
      };
      if (this.selectedTimeLength === "1天") {
        post_timeunit = "days";
        post_timevalue = "1";
        temp_infoLabel = "玩机器直播间1天内zywoo弹幕统计";
      }
      if (this.selectedTimeLength === "历史统计") {
        post_timeunit = "days";
        post_timevalue = "100000";
        temp_infoLabel = "玩机器直播间历史zywoo弹幕统计";
      }

      const data = {
        platform: "douyu",
        room_id: "6979222",
        timeunit: post_timeunit,
        timevalue: post_timevalue
      };

      try {
        this.infoLabel = "正在更新，请不要重复点击~";
        const response = await axios.post('https://media.axuan.wang/zywoo', data);
        
        if (response.data["data_status"] === "Full Pass."){
          if (this.infoNameDict[this.selectedInfoName] == "danmaku"){
            names = response.data["origin_data"]["showinfos"][0];
            values = response.data["origin_data"]["counts"][0];
            last_update = response.data["last_update"];
          }
          else{
            names = response.data["origin_data"]["showinfos"][1];
            values = response.data["origin_data"]["counts"][1];
            last_update = response.data["last_update"];
          }
        
        if (this.selectedTimeLength === "1分钟") {
          temp_infoLabel = "玩机器直播间"+last_update+"之前1分钟zywoo弹幕统计";
        };
        if (this.selectedTimeLength === "1小时") {
          temp_infoLabel = "玩机器直播间"+last_update+"之前1小时zywoo弹幕统计";
        };
        if (this.selectedTimeLength === "1天") {
          temp_infoLabel = "玩机器直播间"+last_update+"之前一天zywoo弹幕统计";
        }
        if (this.selectedTimeLength === "历史统计") {
          temp_infoLabel = "玩机器直播间"+last_update+"之前历史zywoo弹幕统计";
        }

          this.infoLabel = temp_infoLabel;
          // 将名称和数值组合成表格数据
          this.tableData = names.map((name, index) => ({
            name,
            value: values[index],
          }));
          
          // 重置页码
          this.currentPage = 1;
        }
        else if (response.data["data_status"] === "Live Room not Exist.") {
          this.infoLabel = "No Room.";
        }
        else if (response.data["data_status"] === "No Avail Data in This Time Range."){
          this.infoLabel = "短时间内暂无数据~";
        };

      } catch (error) {
        console.error('请求失败:', error);
        // alert('数据请求失败');
        this.infoLabel = "请求失败";
        this.tableData = [].map((name, index) => ({
          name,
          value: [][index],
        }));
      }
    },
    // 复制到剪贴板
    copyToClipboard(value) {
      navigator.clipboard
        .writeText(value.toString())
        .then(() => {
          alert('已复制到剪贴板: ' + value);
        })
        .catch((err) => {
          console.error('复制失败:', err);
          alert('复制失败');
        });
    },
    // 上一页
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
    // 下一页
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },
  },
  mounted() {
    // 初始化时加载数据
    document.title = "玩机器直播间zywoo弹幕统计";
    this.fetchData();
  },
};
</script>

<style scoped>

/* 全局样式 */
body, html {
  margin: 0;
  padding: 0;
  height: 100%;
}

.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: relative; /* 为导航栏定位 */
}

/* 右上角导航栏 */
.navbar {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 15px;
  align-items: center;
}

.nav-link {
  text-decoration: none;
  color: #007bff;
  font-weight: bold;
}

.nav-link:hover {
  text-decoration: underline;
}

.sponsor-img {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

/* 上部 15%：时间尺度、时间单位和确定按钮 */
.top-section {
  height: 12%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-bottom: 1px solid #ccc;
  padding: 0px;
}

.top-section h1 {
  margin: 0;
  margin-bottom: 10px;
}

.form {
  width: 100%;
  display: flex;
  justify-content: center;
}

.form-row {
  display: flex;
  gap: 5px;
  align-items: center;
}

.form-info {
  display: flex;
  align-items: center;
  gap: 5px;
}

.form-group {
  display: flex;
  align-items: center;
  gap: 5px;
}

.top-select {
  width: 120px;
  height: 35px;
}

label {
  font-weight: bold;
}

button {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: #007bff;
  color: white;
  cursor: pointer;
  width: 60px;
}

button:hover {
  background-color: #0056b3;
}

/* 中部 10%：推广信息 */
.mid-section {
  height: 5%;
  padding: 0px;
  width: 1080px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.mid-background{
  padding: 0px;
  background-color: #00fff7;
  color: white;
  cursor: pointer;
  width: 80%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

/* 下部 85%：结果表格 */
.bottom-section {
  height: 85%;
  padding: 0px;
  overflow-y: auto; /* 允许滚动 */
}

.table-container {
  width: 100%;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 10px;
  border: 1px solid #ccc;
  text-align: center;
}

th {
  background-color: #f5f5f5;
}

/* 分页控件 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
}

.pagination button {
  padding: 5px 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

/* 赞助弹框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  position: relative;
}

.sponsor-image {
  max-width: 100%;
  max-height: 80vh;
  border-radius: 8px;
}

.close-button {
  margin-top: 10px;
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.close-button:hover {
  background-color: #0056b3;
}

@media (max-width: 768px) {
.top-section {
  height: 22%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-bottom: 1px solid #ccc;
  padding: 10px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 5px;
  align-items: center;
}

.form-info {
  display: none;
}

.bottom-section {
  height: 78%;
  padding: 20px;
  overflow-y: auto; /* 允许滚动 */
}
}

</style>