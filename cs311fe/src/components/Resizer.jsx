import React from 'react';

const Resizer = ({ onMouseDown }) => {
  return (
    <div
      onMouseDown={onMouseDown}
      style={{
        width: '10px',
        height: '100%',
        cursor: 'ew-resize', // East-West resize for vertical bar
        background: '#e5e7eb',
        borderLeft: '1px solid #d1d5db',
        borderRight: '1px solid #d1d5db',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      <div style={{
        width: '4px',
        height: '40px',
        background: '#9ca3af',
        borderRadius: '2px'
      }}></div>
    </div>
  );
};

export default Resizer;
