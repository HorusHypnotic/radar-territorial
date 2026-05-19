export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.5"
  }
  public: {
    Tables: {
      alert_rules: {
        Row: {
          active: boolean
          condition: Json
          created_at: string
          description: string | null
          id: string
          name: string
          severity: string
        }
        Insert: {
          active?: boolean
          condition: Json
          created_at?: string
          description?: string | null
          id?: string
          name: string
          severity?: string
        }
        Update: {
          active?: boolean
          condition?: Json
          created_at?: string
          description?: string | null
          id?: string
          name?: string
          severity?: string
        }
        Relationships: []
      }
      data_sources: {
        Row: {
          active: boolean
          created_at: string
          id: string
          jurisdiction: string | null
          kind: string
          licitude: string
          name: string
          reliability_score: number
          responsible: string | null
          retention_days: number
          slug: string
          updated_at: string
          url: string | null
        }
        Insert: {
          active?: boolean
          created_at?: string
          id?: string
          jurisdiction?: string | null
          kind: string
          licitude?: string
          name: string
          reliability_score?: number
          responsible?: string | null
          retention_days?: number
          slug: string
          updated_at?: string
          url?: string | null
        }
        Update: {
          active?: boolean
          created_at?: string
          id?: string
          jurisdiction?: string | null
          kind?: string
          licitude?: string
          name?: string
          reliability_score?: number
          responsible?: string | null
          retention_days?: number
          slug?: string
          updated_at?: string
          url?: string | null
        }
        Relationships: []
      }
      governance_logs: {
        Row: {
          action: string
          actor: string | null
          created_at: string
          id: string
          payload: Json
          source_id: string | null
          target_id: string | null
          target_table: string | null
        }
        Insert: {
          action: string
          actor?: string | null
          created_at?: string
          id?: string
          payload?: Json
          source_id?: string | null
          target_id?: string | null
          target_table?: string | null
        }
        Update: {
          action?: string
          actor?: string | null
          created_at?: string
          id?: string
          payload?: Json
          source_id?: string | null
          target_id?: string | null
          target_table?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "governance_logs_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "data_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      licenses: {
        Row: {
          created_at: string
          entity_id: string | null
          event_id: string | null
          id: string
          issued_at: string | null
          license_number: string | null
          license_type: string | null
          raw: Json
        }
        Insert: {
          created_at?: string
          entity_id?: string | null
          event_id?: string | null
          id?: string
          issued_at?: string | null
          license_number?: string | null
          license_type?: string | null
          raw?: Json
        }
        Update: {
          created_at?: string
          entity_id?: string | null
          event_id?: string | null
          id?: string
          issued_at?: string | null
          license_number?: string | null
          license_type?: string | null
          raw?: Json
        }
        Relationships: [
          {
            foreignKeyName: "licenses_entity_id_fkey"
            columns: ["entity_id"]
            isOneToOne: false
            referencedRelation: "urban_entities"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "licenses_event_id_fkey"
            columns: ["event_id"]
            isOneToOne: false
            referencedRelation: "urban_events"
            referencedColumns: ["id"]
          },
        ]
      }
      neighborhoods: {
        Row: {
          centroid_lat: number | null
          centroid_lng: number | null
          city: string
          created_at: string
          id: string
          name: string
          slug: string
          state: string
        }
        Insert: {
          centroid_lat?: number | null
          centroid_lng?: number | null
          city: string
          created_at?: string
          id?: string
          name: string
          slug: string
          state: string
        }
        Update: {
          centroid_lat?: number | null
          centroid_lng?: number | null
          city?: string
          created_at?: string
          id?: string
          name?: string
          slug?: string
          state?: string
        }
        Relationships: []
      }
      permits: {
        Row: {
          created_at: string
          entity_id: string | null
          event_id: string | null
          id: string
          issued_at: string | null
          permit_number: string | null
          permit_type: string | null
          raw: Json
        }
        Insert: {
          created_at?: string
          entity_id?: string | null
          event_id?: string | null
          id?: string
          issued_at?: string | null
          permit_number?: string | null
          permit_type?: string | null
          raw?: Json
        }
        Update: {
          created_at?: string
          entity_id?: string | null
          event_id?: string | null
          id?: string
          issued_at?: string | null
          permit_number?: string | null
          permit_type?: string | null
          raw?: Json
        }
        Relationships: [
          {
            foreignKeyName: "permits_entity_id_fkey"
            columns: ["entity_id"]
            isOneToOne: false
            referencedRelation: "urban_entities"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "permits_event_id_fkey"
            columns: ["event_id"]
            isOneToOne: false
            referencedRelation: "urban_events"
            referencedColumns: ["id"]
          },
        ]
      }
      technical_records: {
        Row: {
          activity: string | null
          art_number: string | null
          created_at: string
          entity_id: string | null
          event_id: string | null
          id: string
          issued_at: string | null
          professional: string | null
          raw: Json
        }
        Insert: {
          activity?: string | null
          art_number?: string | null
          created_at?: string
          entity_id?: string | null
          event_id?: string | null
          id?: string
          issued_at?: string | null
          professional?: string | null
          raw?: Json
        }
        Update: {
          activity?: string | null
          art_number?: string | null
          created_at?: string
          entity_id?: string | null
          event_id?: string | null
          id?: string
          issued_at?: string | null
          professional?: string | null
          raw?: Json
        }
        Relationships: [
          {
            foreignKeyName: "technical_records_entity_id_fkey"
            columns: ["entity_id"]
            isOneToOne: false
            referencedRelation: "urban_entities"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "technical_records_event_id_fkey"
            columns: ["event_id"]
            isOneToOne: false
            referencedRelation: "urban_events"
            referencedColumns: ["id"]
          },
        ]
      }
      territorial_scores: {
        Row: {
          components: Json
          computed_at: string
          id: string
          neighborhood_id: string
          score: number
          trend: number | null
          window_end: string
          window_start: string
        }
        Insert: {
          components?: Json
          computed_at?: string
          id?: string
          neighborhood_id: string
          score: number
          trend?: number | null
          window_end: string
          window_start: string
        }
        Update: {
          components?: Json
          computed_at?: string
          id?: string
          neighborhood_id?: string
          score?: number
          trend?: number | null
          window_end?: string
          window_start?: string
        }
        Relationships: [
          {
            foreignKeyName: "territorial_scores_neighborhood_id_fkey"
            columns: ["neighborhood_id"]
            isOneToOne: false
            referencedRelation: "neighborhoods"
            referencedColumns: ["id"]
          },
        ]
      }
      urban_entities: {
        Row: {
          address: string | null
          company: string | null
          created_at: string
          entity_type: string
          first_seen_at: string
          geocode_confidence: number | null
          geocode_provider: string | null
          id: string
          last_seen_at: string
          lat: number | null
          lng: number | null
          metadata: Json
          name: string | null
          neighborhood_id: string | null
          responsible_technical: string | null
          status: string
          updated_at: string
        }
        Insert: {
          address?: string | null
          company?: string | null
          created_at?: string
          entity_type: string
          first_seen_at?: string
          geocode_confidence?: number | null
          geocode_provider?: string | null
          id?: string
          last_seen_at?: string
          lat?: number | null
          lng?: number | null
          metadata?: Json
          name?: string | null
          neighborhood_id?: string | null
          responsible_technical?: string | null
          status?: string
          updated_at?: string
        }
        Update: {
          address?: string | null
          company?: string | null
          created_at?: string
          entity_type?: string
          first_seen_at?: string
          geocode_confidence?: number | null
          geocode_provider?: string | null
          id?: string
          last_seen_at?: string
          lat?: number | null
          lng?: number | null
          metadata?: Json
          name?: string | null
          neighborhood_id?: string | null
          responsible_technical?: string | null
          status?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "urban_entities_neighborhood_id_fkey"
            columns: ["neighborhood_id"]
            isOneToOne: false
            referencedRelation: "neighborhoods"
            referencedColumns: ["id"]
          },
        ]
      }
      urban_events: {
        Row: {
          bairro_label: string | null
          confidence: number
          created_at: string
          description: string | null
          entity_id: string | null
          event_type: string
          id: string
          lat: number | null
          lng: number | null
          needs_review: boolean
          neighborhood_id: string | null
          occurred_at: string
          payload: Json
          reviewed_at: string | null
          reviewed_by: string | null
          severity: string
          source_id: string | null
          title: string | null
        }
        Insert: {
          bairro_label?: string | null
          confidence?: number
          created_at?: string
          description?: string | null
          entity_id?: string | null
          event_type: string
          id?: string
          lat?: number | null
          lng?: number | null
          needs_review?: boolean
          neighborhood_id?: string | null
          occurred_at?: string
          payload?: Json
          reviewed_at?: string | null
          reviewed_by?: string | null
          severity?: string
          source_id?: string | null
          title?: string | null
        }
        Update: {
          bairro_label?: string | null
          confidence?: number
          created_at?: string
          description?: string | null
          entity_id?: string | null
          event_type?: string
          id?: string
          lat?: number | null
          lng?: number | null
          needs_review?: boolean
          neighborhood_id?: string | null
          occurred_at?: string
          payload?: Json
          reviewed_at?: string | null
          reviewed_by?: string | null
          severity?: string
          source_id?: string | null
          title?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "urban_events_entity_id_fkey"
            columns: ["entity_id"]
            isOneToOne: false
            referencedRelation: "urban_entities"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "urban_events_neighborhood_id_fkey"
            columns: ["neighborhood_id"]
            isOneToOne: false
            referencedRelation: "neighborhoods"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "urban_events_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "data_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      user_roles: {
        Row: {
          created_at: string
          id: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          role?: Database["public"]["Enums"]["app_role"]
          user_id?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      has_role: {
        Args: {
          _role: Database["public"]["Enums"]["app_role"]
          _user_id: string
        }
        Returns: boolean
      }
    }
    Enums: {
      app_role: "admin" | "operator" | "viewer"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      app_role: ["admin", "operator", "viewer"],
    },
  },
} as const
