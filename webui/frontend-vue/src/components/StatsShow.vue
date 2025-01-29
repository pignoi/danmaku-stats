<template>
  <div class="container">
    <!-- 上部 15%：时间尺度、时间单位和确定按钮 -->
    <div class="top-section">
      <div class="form">
        <div class="form-row">
          <div class="form-group">
            <label>平台: {{ platform }}</label>
          </div>
          <div class="form-group">
            <label>房间号: {{ room_id }}</label>
          </div>
          <div class="form-group">
            <label for="timeLength">统计时长:</label>
            <select id="timeLength" v-model="selectedTimeLength">
              <option v-for="option in timeOptions" :key="option" :value="option">
                {{ option }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label for="timeUnit">时间单位:</label>
            <select id="timeUnit" v-model="selectedTimeUnit">
              <option value="minutes">分钟</option>
              <option value="seconds">秒</option>
            </select>
          </div>
          <div class="form-group">
            <button @click="fetchData">确定</button>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>{{ infoLabel }}</label>
          </div>
        </div>
      </div>
    </div>

    <!-- 下部 85%：结果表格 -->
    <div class="bottom-section">

      <div v-if="tableData.length > 0" class="table-container">
        <table>
          <thead>
            <tr>
              <th>弹幕</th>
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
      selectedTimeUnit: 'minutes', // 默认时间单位
      selectedTimeLength: 1, // 默认时间长度
      timeOptions: [1, 2, 5, 30, 600], // 默认时间选项（分钟）
      tableData: [], // 全部表格数据
      currentPage: 1, // 当前页码
      itemsPerPage: 15, // 每页显示的数据条数
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
    // 监听时间单位变化
    selectedTimeUnit(newUnit) {
      if (newUnit === 'minutes') {
        this.timeOptions = [1, 2, 5, 30, 600];
      } else if (newUnit === 'seconds') {
        this.timeOptions = [10, 30];
      }
      this.selectedTimeLength = this.timeOptions[0]; // 重置为第一个选项
      // this.fetchData(); // 自动更新数据
    },
    // 监听时间尺度变化
    selectedTimeLength() {
      this.fetchData(); // 自动更新数据
    },
  },
  methods: {
    // 获取数据
    async fetchData() {
      const data = {
        platform: this.platform,
        room_id: this.room_id,
        timeunit: this.selectedTimeUnit,
        timevalue: this.selectedTimeLength,
      };

      try {
        const response = await axios.post('api/get_by_time', data);
        
        if (response.data["data_status"] === "Full Pass."){
          const names = response.data["origin_data"]["danmakus"];
          const values = response.data["origin_data"]["counts"];
          const last_update = response.data["last_update"];

          this.infoLabel = "最后更新时间: " + last_update;
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
    this.fetchData();
  },
};
</script>

<style>
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
}

/* 上部 15%：时间尺度、时间单位和确定按钮 */
.top-section {
  height: 15%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  /* background-color: #f5f5f5; */
  border-bottom: 1px solid #ccc;
  padding: 10px;
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
  gap: 20px;
  align-items: center;
}

.form-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

label {
  font-weight: bold;
}

select,
button {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  background-color: #007bff;
  color: white;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

/* 下部 85%：结果表格 */
.bottom-section {
  height: 85%;
  padding: 20px;
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
</style>