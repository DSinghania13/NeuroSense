export const getBadgeStatusColor = (status) => {
  const normStatus = status.toLowerCase();
  if (normStatus.includes("alzheimer's") || normStatus.includes('high')) {
    return 'bg-red-100 text-risk-high border-red-200';
  }
  if (normStatus.includes('mild') || normStatus.includes('medium')) {
    return 'bg-yellow-100 text-risk-medium border-yellow-200';
  }
  return 'bg-green-100 text-risk-low border-green-200';
};

export default function Badge({ status, className = "" }) {
  // THE FIX: If status is undefined, default it to 'Unknown' so .toLowerCase() never crashes!
  const safeStatus = status || 'Unknown';
  const lowerStatus = safeStatus.toLowerCase();

  let bgColor = "bg-gray-100";
  let textColor = "text-gray-800";

  if (lowerStatus.includes('completed') || lowerStatus.includes('low')) {
    bgColor = "bg-green-100";
    textColor = "text-green-800";
  } else if (lowerStatus.includes('processing') || lowerStatus.includes('elevated') || lowerStatus.includes('mci')) {
    bgColor = "bg-yellow-100";
    textColor = "text-yellow-800";
  } else if (lowerStatus.includes('failed') || lowerStatus.includes('high')) {
    bgColor = "bg-red-100";
    textColor = "text-red-800";
  }

  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${bgColor} ${textColor} ${className}`}>
      {safeStatus}
    </span>
  );
}
