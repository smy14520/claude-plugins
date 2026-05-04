/**
 * Base adapter for all messaging channels.
 * Each channel (WeChat, Douyin, etc.) extends this class.
 */
export abstract class ChannelAdapter {
  constructor(
    protected channelId: string,
    protected config: ChannelConfig
  ) {}

  /** Receive and parse an incoming webhook payload into UnifiedMessage */
  abstract parseWebhook(payload: unknown): UnifiedMessage;

  /** Send a message through this channel */
  abstract sendMessage(to: string, message: OutgoingMessage): Promise<SendResult>;

  /** Verify webhook signature */
  abstract verifySignature(payload: unknown, signature: string): boolean;

  /** Get OAuth authorization URL for this channel */
  abstract getAuthUrl(): string;

  /** Exchange auth code for access token */
  abstract exchangeToken(code: string): Promise<TokenResult>;
}

export interface ChannelConfig {
  appId: string;
  appSecret: string;
  webhookUrl: string;
  token?: string;
}

export interface UnifiedMessage {
  channelType: string;
  messageId: string;
  fromUser: string;
  content: string;
  contentType: "text" | "image" | "video" | "link";
  rawPayload: unknown;
  receivedAt: Date;
}

export interface OutgoingMessage {
  content: string;
  contentType: "text" | "image";
  metadata?: Record<string, unknown>;
}

export interface SendResult {
  success: boolean;
  messageId?: string;
  error?: string;
}

export interface TokenResult {
  accessToken: string;
  refreshToken?: string;
  expiresIn: number;
}
