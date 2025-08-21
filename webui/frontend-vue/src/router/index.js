import { createRouter, createWebHistory } from 'vue-router';
import Selection from '../components/Selection.vue'; // 引入你的 Vue 组件
import StatsShow from '../components/StatsShow.vue'; // 引入新界面
import desuwa from '../components/desuwa.vue'; // 引入新界面
import zywoo from '../components/zywoo.vue'; // 引入新界面

const routes = [
  {
    path: '/', // 路由路径
    name: 'Home', // 路由名称
    component: Selection, // 对应的组件
  },
  {
    path: '/stats',
    name: 'stats',
    component: StatsShow,
    props: true, // 允许通过路由传递参数
  },
  {
    path: '/desuwa',
    name: 'desuwa',
    component: desuwa,
    props: true, // 允许通过路由传递参数
  },
  {
    path: '/zywoo',
    name: 'zywoo',
    component: zywoo,
    props: true, // 允许通过路由传递参数
  },
];

const router = createRouter({
  history: createWebHistory(), // 使用 HTML5 历史模式
  routes,
});

export default router;