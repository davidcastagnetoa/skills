import * as Device from "expo-device";
import * as Constants from "expo-constants";
import * as Crypto from "expo-crypto";
import { Dimensions, Platform } from "react-native";

interface DeviceInfo {
  brand: string | null;
  modelName: string | null;
  osName: string;
  osVersion: string | null;
  appVersion: string;
  screenWidth: number;
  screenHeight: number;
  deviceType: Device.DeviceType | null;
}

export function getDeviceInfo(): DeviceInfo {
  const { width, height } = Dimensions.get("screen");
  return {
    brand: Device.brand,
    modelName: Device.modelName,
    osName: Platform.OS,
    osVersion: Device.osVersion,
    appVersion: Constants.default.expoConfig?.version ?? "1.0.0",
    screenWidth: width,
    screenHeight: height,
    deviceType: Device.deviceType,
  };
}

export async function getDeviceFingerprint(): Promise<string> {
  const info = getDeviceInfo();
  const raw = JSON.stringify(info);
  const hash = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    raw
  );
  return hash;
}
