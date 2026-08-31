// 统一的 API 基础地址。
// 部署时可通过 .env 文件中的 VITE_API_BASE 覆盖，例如 VITE_API_BASE=https://api.example.com
export const API_BASE = import.meta.env.VITE_API_BASE || 'https://media.axuan.wang';
