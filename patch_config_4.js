const fs = require('fs');

const filePath = 'webui/frontend/src/pages/ConfigurationPage.tsx';
let content = fs.readFileSync(filePath, 'utf8');

// Replace voiceCommands checkbox
content = content.replace(
`<label className="label cursor-pointer justify-start gap-4">
                  <input
                    type="checkbox"
                    className="toggle toggle-info"
                    checked={config.services.voiceCommands}
                    onChange={handleServiceSwitch}
                    name="voiceCommands"
                  />
                  <div className="flex flex-col">
                    <span className="label-text font-medium text-info">Voice Commands (always-on)</span>
                    <span className="label-text-alt text-base-content/60">Listens for audio using ONNX models via openwakeword</span>
                  </div>
                </label>`,
`<label className="label cursor-pointer justify-start gap-4" htmlFor="toggle-voice-commands">
                  <input
                    id="toggle-voice-commands"
                    type="checkbox"
                    className="toggle toggle-info"
                    checked={config.services.voiceCommands}
                    onChange={handleServiceSwitch}
                    name="voiceCommands"
                  />
                  <div className="flex flex-col">
                    <span className="label-text font-medium text-info">Voice Commands (always-on)</span>
                    <span className="label-text-alt text-base-content/60">Listens for audio using ONNX models via openwakeword</span>
                  </div>
                </label>`);

// Replace restApi checkbox
content = content.replace(
`<label className="label cursor-pointer justify-start gap-4">
                  <input
                    type="checkbox"
                    className="toggle toggle-info"
                    checked={config.services.restApi}
                    onChange={handleServiceSwitch}
                    name="restApi"
                  />
                  <div className="flex flex-col">
                    <span className="label-text font-medium text-info">REST API Core</span>
                    <span className="label-text-alt text-base-content/60">Maintains backend connections. Required for WebUI.</span>
                  </div>
                </label>`,
`<label className="label cursor-pointer justify-start gap-4" htmlFor="toggle-rest-api">
                  <input
                    id="toggle-rest-api"
                    type="checkbox"
                    className="toggle toggle-info"
                    checked={config.services.restApi}
                    onChange={handleServiceSwitch}
                    name="restApi"
                  />
                  <div className="flex flex-col">
                    <span className="label-text font-medium text-info">REST API Core</span>
                    <span className="label-text-alt text-base-content/60">Maintains backend connections. Required for WebUI.</span>
                  </div>
                </label>`);

fs.writeFileSync(filePath, content);

console.log("ConfigurationPage.tsx patched 4");
