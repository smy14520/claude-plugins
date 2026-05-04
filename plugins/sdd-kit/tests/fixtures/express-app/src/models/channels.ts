/**
 * Channel model — single-table inheritance.
 * Each channel type is a row with type discriminator.
 *
 * Table: channels
 * Columns:
 *   id          BIGINT PRIMARY KEY AUTO_INCREMENT
 *   name        VARCHAR(100) NOT NULL
 *   type        ENUM('wechat', 'douyin') NOT NULL
 *   app_id      VARCHAR(128) NOT NULL
 *   app_secret  VARCHAR(256) NOT NULL
 *   webhook_url VARCHAR(512)
 *   token       VARCHAR(256)
 *   status      ENUM('active', 'inactive') DEFAULT 'active'
 *   created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
 *   updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
 */
export interface Channel {
  id: number;
  name: string;
  type: "wechat" | "douyin";
  appId: string;
  appSecret: string;
  webhookUrl?: string;
  token?: string;
  status: "active" | "inactive";
  createdAt: Date;
  updatedAt: Date;
}

export class ChannelRepository {
  async findById(id: number): Promise<Channel | null> {
    // DB query
    return null;
  }

  async findByType(type: Channel["type"]): Promise<Channel[]> {
    return [];
  }

  async findActive(): Promise<Channel[]> {
    return [];
  }

  async create(data: Omit<Channel, "id" | "createdAt" | "updatedAt">): Promise<Channel> {
    return {} as Channel;
  }

  async update(id: number, data: Partial<Channel>): Promise<void> {}
}
