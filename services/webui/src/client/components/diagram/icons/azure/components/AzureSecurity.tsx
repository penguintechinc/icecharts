import type { SVGProps } from 'react';
import { memo } from 'react';
const SvgAzureSecurity = (props: SVGProps<SVGSVGElement>) => (
  <svg
    id="e50dc341-b883-4e55-8651-97cc0be130ad"
    xmlns="http://www.w3.org/2000/svg"
    width={18}
    height={18}
    viewBox="0 0 18 18"
    {...props}
  >
    <defs>
      <linearGradient
        id="a2eeded5-bd74-4136-ade6-a04d837899ca"
        x1={9}
        y1={16.795}
        x2={9}
        y2={1.205}
        gradientUnits="userSpaceOnUse"
      >
        <stop offset={0} stopColor="#0078d4" />
        <stop offset={0.064} stopColor="#0a7cd7" />
        <stop offset={0.338} stopColor="#2e8ce1" />
        <stop offset={0.594} stopColor="#4897e9" />
        <stop offset={0.822} stopColor="#589eed" />
        <stop offset={1} stopColor="#5ea0ef" />
      </linearGradient>
    </defs>
    <path
      d="M15.5,8.485c0,4.191-5.16,7.566-6.282,8.25a.412.412,0,0,1-.428,0C7.664,16.051,2.5,12.676,2.5,8.485V3.441a.4.4,0,0,1,.4-.4C6.916,2.935,5.992,1.205,9,1.205s2.084,1.73,6.1,1.837a.4.4,0,0,1,.4.4Z"
      fill="url(#a2eeded5-bd74-4136-ade6-a04d837899ca)"
    />
  </svg>
);
const Memo = memo(SvgAzureSecurity);
export default Memo;
