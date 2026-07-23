export interface StoryCharacter {
  id: number;
  business_id: string;
  story_id: number;
  importance: number;
  virtual_ip_id: number;
  virtual_ip_business_id?: string | null;
  virtual_ip_name?: string | null;
  name?: string | null;
  display_name?: string | null;
  character_name?: string | null;
  role_type?: string;
  role?: string | null;
  description?: string | null;
  appearance?: string | null;
  personality?: string;
  background?: string;
  motivation?: string;
  character_arc?: string;
  backstory?: string | null;
  relationships?: Record<string, unknown>;
  arc_summary?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}
