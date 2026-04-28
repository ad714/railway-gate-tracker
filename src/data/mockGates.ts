import { GateSummary } from '../types/gate';

export const MOCK_GATES: GateSummary[] = [
    {
        gateId: '1',
        name: 'Vikhroli Level Crossing',
        locality: 'Mumbai Suburban',
        status: 'CLOSURE_LIKELY',
        confidence: 'HIGH',
        distanceAheadKm: 1.2,
        expectedDelayMin: [8, 12],
        timeWindow: ['7:45 PM', '7:55 PM'],
    },
    {
        gateId: '2',
        name: 'Kanjurmarg Gate S24',
        locality: 'Mumbai Suburban',
        status: 'LIKELY_OPEN',
        confidence: 'MEDIUM',
        distanceAheadKm: 3.5,
    },
    {
        gateId: '3',
        name: 'Bhandup Crossing B12',
        status: 'UNCERTAIN',
        confidence: 'LOW',
        locality: 'Central Line',
        distanceAheadKm: 5.8,
    },
    {
        gateId: '4',
        name: 'Mulund East Crossing',
        locality: 'Central Railway',
        status: 'LIKELY_OPEN',
        confidence: 'HIGH',
        distanceAheadKm: 8.1,
    },
    {
        gateId: '5',
        name: 'Thane North Gate',
        locality: 'Thane West',
        status: 'CLOSED',
        confidence: 'HIGH',
        distanceAheadKm: 12.4,
        expectedDelayMin: [5, 8],
    },
];
