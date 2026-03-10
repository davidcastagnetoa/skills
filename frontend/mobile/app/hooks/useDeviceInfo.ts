import { useState, useEffect } from "react";
import { getDeviceInfo, getDeviceFingerprint } from "../services/deviceFingerprint";

interface DeviceInfoResult {
  brand: string | null;
  modelName: string | null;
  osName: string;
  osVersion: string | null;
  appVersion: string;
  fingerprint: string | null;
  loading: boolean;
}

export function useDeviceInfo(): DeviceInfoResult {
  const [fingerprint, setFingerprint] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const info = getDeviceInfo();

  useEffect(() => {
    getDeviceFingerprint()
      .then(setFingerprint)
      .finally(() => setLoading(false));
  }, []);

  return {
    brand: info.brand,
    modelName: info.modelName,
    osName: info.osName,
    osVersion: info.osVersion,
    appVersion: info.appVersion,
    fingerprint,
    loading,
  };
}
