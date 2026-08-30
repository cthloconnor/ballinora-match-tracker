/* Build the single-file card bundle with esbuild.
 *
 * lit is left external because Home Assistant already provides it at runtime
 * (and that version may differ from the dev one). Everything else is bundled.
 */
import * as esbuild from "esbuild";

const watch = process.argv.includes("--watch");

const options = {
  entryPoints: ["src/ballinora-match-card.js"],
  bundle: true,
  format: "esm",
  target: "es2022",
  outfile: "dist/ballinora-match-card.js",
  external: ["lit"],
  sourcemap: true,
  logLevel: "info",
  charset: "utf8",
};

if (watch) {
  const ctx = await esbuild.context(options);
  await ctx.watch();
} else {
  await esbuild.build(options);
}