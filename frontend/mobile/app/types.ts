/** Shared types for the VerifID mobile app. */

export type VerificationStatus = "VERIFIED" | "REJECTED" | "MANUAL_REVIEW";

export interface ChallengeResult {
  type: "blink" | "turn_left" | "turn_right" | "smile";
  passed: boolean;
  timestampMs: number;
}

export interface VerificationRequest {
  selfieFrames: string[]; // base64 JPEG
  documentImage: string; // base64 JPEG
  deviceFingerprint: string;
  challenges: ChallengeResult[];
}

export interface VerificationResult {
  sessionId: string;
  status: VerificationStatus;
  confidenceScore: number;
  reasons: string[];
  processingTimeMs: number;
}

export interface SessionProgress {
  sessionId: string;
  status: "pending" | "processing" | "completed" | "failed";
  currentPhase: string;
  completedPhases: string[];
  result?: VerificationResult;
}

export type RootStackParamList = {
  Welcome: undefined;
  SelfieCapture: undefined;
  ActiveChallenges: { selfieFrames: string[] };
  DocumentCapture: { selfieFrames: string[]; challenges: ChallengeResult[] };
  Processing: {
    selfieFrames: string[];
    documentImage: string;
    challenges: ChallengeResult[];
  };
  Result: { result: VerificationResult };
};
