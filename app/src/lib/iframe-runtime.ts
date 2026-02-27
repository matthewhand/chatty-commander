export function appendLog(text: string) {
  const pre =
    document.getElementById("console") ||
    document.body.appendChild(document.createElement("pre"));
  pre.id = "console";
  const line = document.createElement("div");
  line.textContent = text;
  pre.appendChild(line);
}
