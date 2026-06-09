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
                  <span className="label-text">
                    <MicIcon size={16} className="inline mr-2" /> Enable Voice Commands
                  </span>
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
                  <span className="label-text">
                    <MicIcon size={16} className="inline mr-2" /> Enable Voice Commands
                  </span>
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
                  <span className="label-text">
                    <ServerIcon size={16} className="inline mr-2" /> Enable REST API (required for Web UI)
                  </span>
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
                  <span className="label-text">
                    <ServerIcon size={16} className="inline mr-2" /> Enable REST API (required for Web UI)
                  </span>
                </label>`);

// Replace select file input
content = content.replace(
`<div className="form-control w-full">
                   <input
                    type="file"
                    accept=".onnx"
                    aria-label="Select ONNX voice model file"
                    className="file-input file-input-bordered file-input-primary file-input-sm w-full"
                    onChange={handleFileUpload}
                    ref={fileInputRef}
                  />
                  <label className="label">
                    <span className="label-text-alt text-base-content/50">Upload an ONNX file directly</span>
                  </label>
                 </div>`,
`<div className="form-control w-full">
                  <label className="label" htmlFor="upload-voice-model">
                    <span className="label-text-alt text-base-content/50">Upload an ONNX file directly</span>
                  </label>
                  <input
                    id="upload-voice-model"
                    type="file"
                    accept=".onnx"
                    aria-label="Select ONNX voice model file"
                    className="file-input file-input-bordered file-input-primary file-input-sm w-full"
                    onChange={handleFileUpload}
                    ref={fileInputRef}
                  />
                 </div>`);

fs.writeFileSync(filePath, content);

console.log("ConfigurationPage.tsx patched 2");
