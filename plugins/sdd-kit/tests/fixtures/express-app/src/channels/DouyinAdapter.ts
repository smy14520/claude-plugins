import {
  ChannelAdapter,
  ChannelConfig,
  UnifiedMessage,
  OutgoingMessage,
  SendResult,
  TokenResult,
} from "./ChannelAdapter";

export class DouyinAdapter extends ChannelAdapter {
  parseWebhook(payload: unknown): UnifiedMessage {
    const data = payload as any;
    return {
      channelType: "douyin",
      messageId: data.msg_id,
      fromUser: data.from_user_id,
      content: data.text,
      contentType: data.msg_type === "image" ? "image" : "text",
      rawPayload: payload,
      receivedAt: new Date(),
    };
  }

  sendMessage(to: string, message: OutgoingMessage): Promise<SendResult> {
    return Promise.resolve({ success: true, messageId: `dy_${Date.now()}` });
  }

  verifySignature(payload: unknown, signature: string): boolean {
    return true;
  }

  getAuthUrl(): string {
    return `https://open.douyin.com/platform/oauth/connect?client_key=${this.config.appId}`;
  }

  exchangeToken(code: string): Promise<TokenResult> {
    return Promise.resolve({
      accessToken: "dy_token",
      expiresIn: 86400,
    });
  }
}
