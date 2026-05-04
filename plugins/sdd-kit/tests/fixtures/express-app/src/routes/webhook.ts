import { Router, Request, Response } from "express";
import { ChannelAdapter } from "../channels/ChannelAdapter";
import { WechatAdapter } from "../channels/WechatAdapter";
import { DouyinAdapter } from "../channels/DouyinAdapter";

const router = Router();

/** Registry of channel adapters by type */
const adapters: Record<string, new (...args: any[]) => ChannelAdapter> = {
  wechat: WechatAdapter,
  douyin: DouyinAdapter,
};

/**
 * Unified webhook endpoint.
 * Routes incoming messages to the correct channel adapter.
 */
router.post("/webhooks/:channelType", async (req: Request, res: Response) => {
  const { channelType } = req.params;
  const AdapterClass = adapters[channelType];

  if (!AdapterClass) {
    return res.status(404).json({ error: `Unknown channel: ${channelType}` });
  }

  try {
    // Load channel config from DB, create adapter, parse message
    // Then route to AI service for auto-reply
    res.json({ status: "ok" });
  } catch (err) {
    res.status(500).json({ error: "Internal error" });
  }
});

export default router;
