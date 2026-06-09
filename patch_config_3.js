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
                    <span className="label-text font-medium flex items-center gap-2">
                      <MicIcon size={16} className="text-info" /> Voice Commands
                    </span>
                    <span className="label-text-alt text-base-content/50 mt-1">Enable listening for wake words and voice execution.</span>
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
                    <span className="label-text font-medium flex items-center gap-2">
                      <MicIcon size={16} className="text-info" /> Voice Commands
                    </span>
                    <span className="label-text-alt text-base-content/50 mt-1">Enable listening for wake words and voice execution.</span>
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
                    <span className="label-text font-medium flex items-center gap-2">
                      <ServerIcon size={16} className="text-info" /> REST API
                    </span>
                    <span className="label-text-alt text-base-content/50 mt-1">Enable local API server. Required for Web UI and remote control.</span>
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
                    <span className="label-text font-medium flex items-center gap-2">
                      <ServerIcon size={16} className="text-info" /> REST API
                    </span>
                    <span className="label-text-alt text-base-content/50 mt-1">Enable local API server. Required for Web UI and remote control.</span>
                  </div>
                </label>`);

fs.writeFileSync(filePath, content);

console.log("ConfigurationPage.tsx patched 3");
