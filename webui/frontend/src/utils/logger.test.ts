import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { logger } from "./logger";

describe("logger", () => {
  beforeEach(() => {
    vi.spyOn(console, "debug").mockImplementation(() => {});
    vi.spyOn(console, "info").mockImplementation(() => {});
    vi.spyOn(console, "warn").mockImplementation(() => {});
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  describe("in DEV", () => {
    beforeEach(() => {
      vi.stubEnv("DEV", true);
    });

    it("emits dbg/info/warn", () => {
      // eslint-disable-next-line testing-library/no-debugging-utils
      // eslint-disable-next-line testing-library/no-debugging-utils
      logger.debug("d");
      logger.info("i");
      logger.warn("w");
      expect(console.debug).toHaveBeenCalledWith("d");
      expect(console.info).toHaveBeenCalledWith("i");
      expect(console.warn).toHaveBeenCalledWith("w");
    });

    it("emits error", () => {
      logger.error("boom");
      expect(console.error).toHaveBeenCalledWith("boom");
    });
  });

  describe("in production (DEV=false)", () => {
    beforeEach(() => {
      vi.stubEnv("DEV", false);
    });

    it("suppresses dbg/info/warn", () => {
      // eslint-disable-next-line testing-library/no-debugging-utils
      logger.debug("d");
      logger.info("i");
      logger.warn("w");
      expect(console.debug).not.toHaveBeenCalled();
      expect(console.info).not.toHaveBeenCalled();
      expect(console.warn).not.toHaveBeenCalled();
    });

    it("still emits error", () => {
      logger.error("boom", { code: 1 });
      expect(console.error).toHaveBeenCalledWith("boom", { code: 1 });
    });
  });
});
