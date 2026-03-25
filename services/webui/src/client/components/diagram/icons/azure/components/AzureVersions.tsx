import type { SVGProps } from 'react';
import { memo } from 'react';
const SvgAzureVersions = (props: SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={18} height={18} viewBox="0 0 18 18" {...props}>
    <defs>
      <linearGradient
        id="e5eb8d49-f596-43cc-8882-1dde4f1785ce"
        x1={7.849}
        y1={12.323}
        x2={7.849}
        y2={4.229}
        gradientUnits="userSpaceOnUse"
      >
        <stop offset={0} stopColor="#0078d4" />
        <stop offset={0.502} stopColor="#4093e6" />
        <stop offset={0.775} stopColor="#5ea0ef" />
      </linearGradient>
      <linearGradient
        id="b27ee86e-b59d-4418-8747-06a34580fa30"
        x1={10.151}
        y1={16.69}
        x2={10.151}
        y2={8.595}
        gradientUnits="userSpaceOnUse"
      >
        <stop offset={0} stopColor="#32bedd" />
        <stop offset={0.175} stopColor="#32caea" />
        <stop offset={0.41} stopColor="#32d2f2" />
        <stop offset={0.775} stopColor="#32d4f5" />
      </linearGradient>
    </defs>
    <title>{'MsPortalFx.base.images-19'}</title>
    <g id="bc5e6cd2-d956-42f3-a793-ab65f89250a4">
      <g>
        <path
          d="M1,4.229H14.7a0,0,0,0,1,0,0v7.637a.458.458,0,0,1-.458.458H1.458A.458.458,0,0,1,1,11.866V4.229A0,0,0,0,1,1,4.229Z"
          fill="url(#e5eb8d49-f596-43cc-8882-1dde4f1785ce)"
        />
        <path
          d="M1.46,1.31H14.237a.458.458,0,0,1,.458.458V4.229a0,0,0,0,1,0,0H1a0,0,0,0,1,0,0V1.768A.458.458,0,0,1,1.46,1.31Z"
          fill="#0078d4"
        />
        <path
          d="M3.3,8.6H17a0,0,0,0,1,0,0v7.637a.458.458,0,0,1-.458.458H3.76a.458.458,0,0,1-.458-.458V8.6A0,0,0,0,1,3.3,8.6Z"
          fill="url(#b27ee86e-b59d-4418-8747-06a34580fa30)"
        />
        <path
          d="M3.763,5.677H16.54A.458.458,0,0,1,17,6.134V8.6a0,0,0,0,1,0,0H3.3a0,0,0,0,1,0,0V6.134A.458.458,0,0,1,3.763,5.677Z"
          fill="#198ab3"
        />
      </g>
    </g>
  </svg>
);
const Memo = memo(SvgAzureVersions);
export default Memo;
