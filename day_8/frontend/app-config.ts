export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'HealthSathi',
  pageTitle: 'HealthSathi — Your friendly voice companion for everyday health guidance',
  pageDescription:
    'HealthSathi helps you understand symptoms, prepare for doctor visits, set medication reminders, and access health guidance in your language — English, Hindi, or Hinglish.',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/healthsathi-logo.svg',
  accent: 'hsl(173, 58%, 39%)',
  logoDark: '/healthsathi-logo.svg',
  accentDark: 'hsl(173, 58%, 55%)',
  startButtonText: '🩺 Talk to HealthSathi',

  audioVisualizerType: 'aura',
  audioVisualizerColor: '#1A9E8F',
  audioVisualizerColorDark: '#2DD4BF',
  audioVisualizerColorShift: 0.2,

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
