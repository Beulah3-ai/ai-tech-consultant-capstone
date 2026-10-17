import dotenv from "dotenv";
import { createApp } from "./app.js";

dotenv.config();

const port = parseInt(process.env.PORT || "3000", 10);
const app = createApp();

app.listen(port, () => {
  console.log(`=======================================================`);
  console.log(` Inbox Agent (Task 2) running on http://localhost:${port}`);
  console.log(` Connected Knowledge Brain: ${process.env.KNOWLEDGE_BRAIN_URL || "http://localhost:8000"}`);
  console.log(` Human Review UI: http://localhost:${port}`);
  console.log(`=======================================================`);
});
