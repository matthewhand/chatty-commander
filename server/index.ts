import express from "express";
import cors from "cors";
import chat from "./routes/chat.js";
import canvas from "./routes/canvas.js";
import consoleRoute from "./routes/console.js";
import sidecar from "./routes/sidecar.js";
import { csp } from "./middleware/csp.js";

const app = express();
app.use(cors());
app.use(csp);
app.use(express.json());

app.use("/api/chat", chat);
app.use("/api/canvas", canvas);
app.use("/api/console", consoleRoute);
app.use("/api/sidecar", sidecar);

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`server on ${port}`));
