import React from 'react';

interface DashboardProps {
  title: string;
}

export const Dashboard: React.FC<DashboardProps> = ({ title }) => {
  return (
    <div>
      <h1>{title}</h1>
      <p>Welcome to the dashboard</p>
    </div>
  );
};
