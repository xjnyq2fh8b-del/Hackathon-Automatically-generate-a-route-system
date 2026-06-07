import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = dirname(fileURLToPath(import.meta.url));
const projectRoot = resolve(frontendDir, "..");

function readLocalEnv(filePath) {
  if (!existsSync(filePath)) return {};
  return Object.fromEntries(
    readFileSync(filePath, "utf8")
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#") && line.includes("="))
      .map((line) => {
        const index = line.indexOf("=");
        const key = line.slice(0, index).trim();
        const value = line.slice(index + 1).trim().replace(/^['"]|['"]$/g, "");
        return [key, value];
      }),
  );
}

const localEnv = {
  ...readLocalEnv(resolve(projectRoot, ".env.local")),
  ...readLocalEnv(resolve(frontendDir, ".env.local")),
};

const env = {
  VITE_AMAP_KEY: process.env.VITE_AMAP_KEY || localEnv.VITE_AMAP_KEY || "",
  VITE_AMAP_SECURITY_JS_CODE:
    process.env.VITE_AMAP_SECURITY_JS_CODE || localEnv.VITE_AMAP_SECURITY_JS_CODE || "",
};

writeFileSync(
  resolve(frontendDir, "src", "config.generated.js"),
  `window.ROUTE_AGENT_ENV = ${JSON.stringify(env, null, 2)};\n`,
);

console.log("Generated frontend map config.");
