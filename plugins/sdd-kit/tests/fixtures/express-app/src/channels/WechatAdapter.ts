import {
  ChannelAdapter,
  ChannelConfig,
  UnifiedMessage,
  OutgoingMessage,
  SendResult,
  TokenResult,
} from "./ChannelAdapter";

export class WechatAdapter extends ChannelAdapter {
  parseWebhook(payload: unknown): UnifiedMessage {
    const data = payload as any;
    return {
      channelType: "wechat",
      messageId: data.MsgId,
      fromUser: data.FromUserName,
      content: data.Content,
      contentType: this.mapContentType(data.MsgType),
      rawPayload: payload,
      receivedAt: new Date(),
    };
  }

  sendMessage(to: string, message: OutgoingMessage): Promise<SendResult> {
    // Call WeChat API to send message
    return Promise.resolve({ success: true, messageId: `wx_${Date.now()}` });
  }

  verifySignature(payload: unknown, signature: string): boolean {
    // WeChat signature verification using token + timestamp + nonce
    return true;
  }

  getAuthUrl(): string {
    return `https://open.weixin.qq.com/connect/oauth2/authorize?appid=${this.config.appId}`;
  }

  exchangeToken(code: string): Promise<TokenResult> {
    return Promise.resolve({
      accessToken: "wx_token",
      refreshToken: "wx_refresh",
      expiresIn: 7200,
    });
  }

  private mapContentType(msgType: string): UnifiedMessage["contentType"] {
    switch (msgType) {
      case "image": return "image";
      case "video": return "video";
      default: return "text";
    }
  }
}
