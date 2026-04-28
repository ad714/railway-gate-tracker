/**
 * Smart Naming Utility for RGT V2
 * 
 * Instead of displaying obscure gate numbers, this utility generates
 * user-friendly names based on proximity to stations and localities.
 */

export interface StationInfo {
    name: string;
    distance: number;
}

/**
 * Generates a contextual name for a railway gate.
 * @param gateId The official gate number/ID
 * @param station The nearest station information
 * @param locality The general locality or area name
 * @returns A formatted string like "Gate near Sasthankotta Station"
 */
export const generateSmartGateName = (
    gateId: string,
    station: StationInfo,
    locality?: string
): string => {
    const stationName = station.name.replace(' (halt)', '').trim();

    // If very close to a station, name it as the Station Gate
    if (station.distance < 0.3) {
        return `${stationName} Station Gate`;
    }

    // If moderately close, use "Gate near [Station]"
    if (station.distance < 1.5) {
        return `Gate near ${stationName} Station`;
    }

    // If locality is provided and station is far, use Locality + Gate ID
    if (locality) {
        return `${locality} Gate ${gateId}`;
    }

    // Fallback to basic naming
    return `Railway Gate ${gateId} (${stationName})`;
};

/**
 * Simple Haversine distance calculator (in KM)
 */
export const calculateDistance = (
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
): number => {
    const R = 6371; // Earth radius
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
};
