import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { GateStatus } from '../types/gate';

interface StatusBadgeProps {
    status: GateStatus;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
    const getStyles = () => {
        switch (status) {
            case 'LIKELY_OPEN':
                return { label: 'LIKELY OPEN', container: styles.openContainer, text: styles.openText };
            case 'CLOSURE_LIKELY':
                return { label: 'CLOSURE LIKELY', container: styles.amberContainer, text: styles.amberText };
            case 'CLOSED':
                return { label: 'CLOSED', container: styles.closedContainer, text: styles.closedText };
            case 'UNCERTAIN':
            default:
                return { label: 'STATUS UNCERTAIN', container: styles.uncertainContainer, text: styles.uncertainText };
        }
    };

    const { label, container, text } = getStyles();

    return (
        <View style={[styles.baseContainer, container]}>
            <Text style={[styles.baseText, text]}>{label}</Text>
        </View>
    );
};

const styles = StyleSheet.create({
    baseContainer: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 16,
        borderWidth: 1,
    },
    baseText: {
        fontSize: 10,
        fontWeight: '800',
        letterSpacing: 0.5,
    },
    openContainer: {
        backgroundColor: '#ecfdf5',
        borderColor: '#d1fae5',
    },
    openText: {
        color: '#059669',
    },
    amberContainer: {
        backgroundColor: '#fffbeb',
        borderColor: '#fef3c7',
    },
    amberText: {
        color: '#d97706',
    },
    closedContainer: {
        backgroundColor: '#fef2f2',
        borderColor: '#fee2e2',
    },
    closedText: {
        color: '#dc2626',
    },
    uncertainContainer: {
        backgroundColor: '#f8fafc',
        borderColor: '#f1f5f9',
    },
    uncertainText: {
        color: '#64748b',
    },
});

export default StatusBadge;
