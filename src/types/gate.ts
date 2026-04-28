export type GateStatus =
    | 'LIKELY_OPEN'
    | 'CLOSURE_LIKELY'
    | 'CLOSED'
    | 'UNCERTAIN';

export type Confidence = 'LOW' | 'MEDIUM' | 'HIGH';

export interface GateSummary {
    gateId: string;
    name: string;
    locality: string;
    distanceAheadKm: number;
    status: GateStatus;
    expectedDelayMin?: [number, number];
    timeWindow?: [string, string];
    confidence: Confidence;
}

export interface RouteSummary {
    origin: string;
    destination: string;
    baseTravelTime: string;
    estimatedDelayRange: string;
}
