<template>
  <div class="container">
    <div class="form">
      <label for="platform">选择平台:</label>
      <select id="platform" v-model="selectedPlatform">
        <option value="bilibili">bilibili</option>
        <option value="douyu">斗鱼</option>
      </select>

      <label for="number">输入房间号:</label>
      <input
        id="number"
        type="number"
        v-model="inputNumber"
        @keyup.enter="submitData"
      />

      <button @click="submitData">确定</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      selectedPlatform: 'douyu', // 默认选择 douyu
      inputNumber: null, // 数字输入框的值
    };
  },
  methods: {
    async submitData() {
      if (this.inputNumber === null || isNaN(this.inputNumber)) {
        alert('请输入有效的数字');
        return;
      }

      const data = {
        platform: this.selectedPlatform,
        room_id: this.inputNumber,
      };

      try {
        const response = await axios.post('https://media.axuan.wang/check', data);
        console.log('提交成功');

        if (response.data['message'] === "yes") {
          this.$router.push({
            name: 'stats',
            query: { platform: data.platform, room_id: data.room_id },
          });
        } else if (response.data['message'] === "yes") {
          alert('没有收集该直播间的信息~');
        }
      } catch (error) {
        console.error('提交失败:', error);
        alert('数据提交失败');
      }
    },
  },
  mounted() {
    // 初始化时加载数据
    document.title = "首页";
  },
};
</script>

<style>
/* 居中布局 */
.container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  /* width: 50%; */
}

.form {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  gap: 10px;
  width: 300px;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

label {
  font-weight: bold;
}

input,
select,
button {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 150px;
}

button {
  background-color: #007bff;
  color: white;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}
</style>