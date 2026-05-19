import { createServerFn } from "@tanstack/react-start";
import { buildSnapshot } from "./radar.server";

export const getDashboardSnapshot = createServerFn({ method: "GET" }).handler(async () => {
  return buildSnapshot();
});
